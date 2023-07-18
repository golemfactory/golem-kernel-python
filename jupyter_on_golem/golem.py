import asyncio
import base64
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from random import random, randint
from subprocess import check_output, check_call

import aiohttp
import async_timeout
from golem_core.core.golem_node import GolemNode
from golem_core.pipeline import Chain, Map, Buffer
from golem_core.core.market_api import ManifestVmPayload
from golem_core.core.market_api.pipeline import default_negotiate, default_create_agreement, default_create_activity
import humanize
from pytimeparse import parse as parse_to_seconds
import websockets

from .remote_python import RemotePython
from . import TMPDIR_PATH

KERNEL_IMAGE_TAG = 'jupyter-on-golem/python-kernel:latest'

YAGNA_APPNAME_JUPYTER = 'jupyterongolem'
SPINNER_SVG = '<svg {spinner_class} width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><style>.spinner_9y7u{{animation:spinner_fUkk 2.4s linear infinite;animation-delay:-2.4s}}.spinner_DF2s{{animation-delay:-1.6s}}.spinner_q27e{{animation-delay:-.8s}}@keyframes spinner_fUkk{{8.33%{{x:13px;y:1px}}25%{{x:13px;y:1px}}33.3%{{x:13px;y:13px}}50%{{x:13px;y:13px}}58.33%{{x:1px;y:13px}}75%{{x:1px;y:13px}}83.33%{{x:1px;y:1px}}}}</style><rect class="spinner_9y7u" x="1" y="1" rx="1" width="10" height="10"/><rect class="spinner_9y7u spinner_DF2s" x="1" y="1" rx="1" width="10" height="10"/><rect class="spinner_9y7u spinner_q27e" x="1" y="1" rx="1" width="10" height="10"/></svg>'

YAGNA_NOT_FOUND_HTML_MESSAGE = '''\
<span style="color: red; font-weight: bold;">WARNING</span>: Yagna executable was not found.
<br/>
Please install Golem first: <a href="https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development">Installation guide</a>
</p>
'''

STATUS_TEMPLATE = '''\
My node ID: {node_id}
My wallet address: {node_id}
{polygon_status}
{goerli_status}
Connection status: {connection_status}
{provider_info}{connection_time}
'''

HELP_TEMPLATE = '''\
     _                   _                             ____       _                
    | |_   _ _ __  _   _| |_ ___ _ __    ___  _ __    / ___| ___ | | ___ _ __ ___  
 _  | | | | | '_ \| | | | __/ _ \ '__|  / _ \| '_ \  | |  _ / _ \| |/ _ \ '_ ` _ \ 
| |_| | |_| | |_) | |_| | ||  __/ |    | (_) | | | | | |_| | (_) | |  __/ | | | | |
 \___/ \__,_| .__/ \__, |\__\___|_|     \___/|_| |_|  \____|\___/|_|\___|_| |_| |_| version: 0.1.3
            |_|    |___/                                                           

Easy to use tool to run Your Jupyter Notebooks on the Golem Network!

COMMANDS:    
    %status		Shows current status of Jupyter on Golem
    %fund		Requests for testnet funds, e.g. '%fund goerli'
    %budget		Allocates GLM tokens for payments, e.g. '%budget goerli 2'. Available networks: goerli, polygon, mainnet.
    %connect		Looks for Provider which meets with defined criteria [mem|cores|disk], e.g. '%connect mem>1'				
    %disconnect 	Disconnects from the currently active Provider
    %download	 	Downloads file from Provider's ./workdir folder to local machine, e.g. '%download dataset.csv'
    %upload		Uploads file from local machine into Provider's ./workdir folder, e.g. '%upload results.csv'
    %help		Shows this message    
    %pip install        Installs PyPI package on the Provider's host, e.g. "%pip install colorama"

'''

PROVIDER_TEMPLATE = '''\
Connected to {provider_name} [{provider_id}]
    RAM: {ram} GB
    DISK: {disk} GB
    CPU: {cpu} cores
'''


class YagnaNotFound(Exception):
    pass


async def negotiate(proposal):
    return await asyncio.wait_for(default_negotiate(proposal), timeout=5)


async def bestprice_score(proposal):
    properties = proposal.data.properties
    if properties['golem.com.pricing.model'] != 'linear':
        return None

    coeffs = properties['golem.com.pricing.model.linear.coeffs']
    return 1 - (coeffs[0] + coeffs[1])


async def random_score(proposal):
    return random()

STRATEGY_SCORING_FUNCTION = {"bestprice": bestprice_score, "random": random_score}
DEFAULT_SCORING_STRATEGY = "bestprice"
DEFAULT_CONNECTION_TIMEOUT = timedelta(minutes=10)


class Golem:
    def __init__(self):
        self._golem_node = None
        self._allocation = None
        self._remote_python = None

        #   The loop where GolemNode is running, we need it in aclose()
        self._loop = None

    ####################
    #   PUBLIC API
    @property
    def connected(self):
        return self._remote_python is not None

    async def execute(self, code):
        """Yields tuples (message, is_result).

        This is not perfect, but good enough for a simple live updates (e.g. in %fund).
        This will probably change in a significant way if we decide to pass raw messages
        from the kernel.
        """
        local_commands = ('%status', '%help', '%fund', '%budget', '%connect', '%disconnect', '%upload', '%download')

        if any(code.startswith(command) for command in local_commands):
            try:
                async for out in self._run_local_command(code):
                    yield out, False
            except YagnaNotFound:
                yield {
                    "type": "display_data",
                    "content": {
                        "text/plain": "<IPython.core.display.HTML object>",
                        "text/html": YAGNA_NOT_FOUND_HTML_MESSAGE,
                    }
                }, False
            except Exception as e:
                yield f"Error running a local command: {e}", False
        elif not self.connected:
            yield f"Provider not connected. Available commands: {', '.join(local_commands)}.", False
        else:
            try:
                async for out in self._alter_and_run_remote_command(code):
                    yield out
            except websockets.ConnectionClosedError:
                yield "Encountered connection problem with provider.", False
                async for out in self._run_local_command('%disconnect'):
                    yield out, False

    async def aclose(self):
        #   NOTE: We don't wait for invoices here.
        #         We could easily use golem_core.default_payment_manager.DefaultPaymentManager,
        #         but this doesn't make much sense now - payments/invoices require some separate solution.
        if self._golem_node is not None:
            #   Q: Why this?
            #   A: Current running loop is different than the loop that was running when GolemNode
            #      was started. We must use the latter to stop the GolemNode.
            fut = asyncio.run_coroutine_threadsafe(self._golem_node.aclose(), self._loop)
            fut.result()

    ####################
    #   INTERNALS

    def _validate_yagna_exists(self) -> bool:
        try:
            check_call(["yagna", "--version"])
            return True
        except Exception:
            raise YagnaNotFound

    async def _run_local_command(self, code):
        if not code.startswith('%help'):
            self._validate_yagna_exists()

        if code == '%status':
            yield self._get_status_text()
        elif code == '%help':
            yield self._get_help_text()
            self._validate_yagna_exists()
        elif code.startswith('%fund'):
            network = code.split()[1]
            yield "Waiting for funds\n"
            yield self._get_spinner_content_dict()
            try:
                self._get_funds(network)
            except Exception:
                yield {"type": "clear_output"}
                yield "Funding failed"
            else:
                yield {"type": "clear_output"}
                yield self._get_network_status_text(network) + "\n"
                yield self._get_budget_text()
        elif code.startswith('%budget'):
            network, amount = code.split()[1:]
            amount = float(amount)
            await self._create_allocation(network, amount)
            yield self._get_budget_text()
        elif code.startswith('%connect'):
            if not self._allocation:
                yield self._get_budget_text()
            elif self.connected:
                yield "Already connected\n"
            else:
                try:
                    args_str = code.split(maxsplit=1)[1]
                except IndexError:
                    args_str = ''

                yield "Progress: 1/4\n" \
                      f"    Resolving image tag: {KERNEL_IMAGE_TAG}..."
                try:
                    image_details = await self._get_kernel_image_details()
                except aiohttp.ClientResponseError:
                    yield " Failed!\n"
                else:
                    yield " Ok.\n"
                    payload, offer_scorer, timeout = await self._parse_connect_args(args_str, image_details)
                    async for out in self._connect(payload, offer_scorer, timeout):
                        yield out
        elif code.startswith('%disconnect'):
            connection_time = self._get_connection_time()
            if not self.connected:
                yield "No connected provider"
            else:
                yield "Disconnecting... "
                invoice_amount = await self._disconnect_and_pay()
                yield "done.\n" \
                      f"Connection time: {connection_time}\n"

                if invoice_amount is None:
                    yield "Invoice is missing, paid nothing.\n"
                else:
                    yield f"Total cost: {invoice_amount}\n"
                yield self._get_budget_text()
        elif code.startswith('%upload'):
            if not self.connected:
                yield "No connected provider."
            else:
                try:
                    file_path = code.split(maxsplit=1)[1]
                except IndexError:
                    yield "Provide file path to upload."
                else:
                    if Path(file_path).exists():
                        yield "Sending...\n"
                        await self._remote_python.upload_file(file_path)
                        yield "File uploaded.\n"
                    else:
                        yield "File does not exist."
        elif code.startswith('%download'):
            if not self.connected:
                yield "No connected provider."
            else:
                try:
                    file_path = code.split(maxsplit=1)[1]
                except IndexError:
                    yield "Provide file path to upload."
                else:
                    yield "Downloading...\n"
                    await self._remote_python.download_file(file_path)
                    yield "File downloaded.\n"
        else:
            raise ValueError(f"Unknown command: {code}")

    async def _alter_and_run_remote_command(self, code):
        """ Altering PIP behaviour:
          - running command with special parameters so pip is using right directories for temp data
          - displaying spinner while pip is running
        """

        if code.startswith('%pip install'):
            # New Pip versions doesn't support --build option.
            # Since Pip 21.3 it relies on TMPDIR env var. Can additionally use --no-clean.
            code = f'{code} --build {TMPDIR_PATH} --no-cache-dir'
            yield self._get_spinner_content_dict(), False
            async for content, is_result in self._run_remote_command(code):
                if not is_result:
                    yield {"type": "clear_output"}, False
                yield content, is_result
        else:
            async for out in self._run_remote_command(code):
                yield out

    def _get_spinner_content_dict(self, html_class=None):
        spinner_class = f'class="{html_class}"' if html_class else ''
        return {
            "type": "display_data",
            "content": {
                "text/plain": "<IPython.core.display.HTML object>",
                "text/html": SPINNER_SVG.format(spinner_class=spinner_class),
            }
        }

    def _get_spinner_hide_css(self, spinner_class):
        return {
            "type": "display_data",
            "content": {
                "text/plain": "<IPython.core.display.HTML object>",
                "text/html": f"<style>." + spinner_class + "{display: none !important}</style>",
            }
        }

    async def _run_remote_command(self, code):
        result = await self._remote_python.execute(code)
        if "stdout" in result:
            yield result["stdout"], False
        if "result" in result:
            yield result["result"], True

    def _get_funds(self, network):
        check_call(["yagna", "payment", "fund", "--network", network], timeout=60)

    async def _create_allocation(self, network, amount):
        if self._allocation is not None:
            await self._allocation.release()
            self._allocation = None

        if self._golem_node is None:
            self._loop = asyncio.get_running_loop()
            self._golem_node = GolemNode(self._get_or_create_yagna_appkey())
            await self._golem_node.start()

        check_call(["yagna", "payment", "init", "--network", network])
        check_call(["yagna", "payment", "init", "--network", network, "--sender"])

        self._allocation = await self._golem_node.create_allocation(amount, network)
        await self._allocation.get_data()

    async def _connect(self, payload, offer_scorer, timeout):
        try:
            async with async_timeout.timeout(int(timeout.total_seconds())):
                yield f"Progress: 2/4\n" \
                      "    Demand created. Waiting for counter proposal.\n" \
                      f"    Searching for {self._payload_text(payload)}...\n" \
                      f"    Will try to connect for {humanize.naturaldelta(timeout)}.\n"

                spinner_1_class = f'connect-1-{randint(100, 999)}'
                yield self._get_spinner_content_dict(spinner_1_class)

                async for activity in self._get_activity(payload, offer_scorer):
                    yield "Progress: 3/4\n" \
                          "    Agreement created.\n" \
                          f"    {self._provider_info_text(activity)}" \
                          "Progress: 4/4\n" \
                          "    Engine is starting. Depending on provider, it might take few to ~10 minutes...\n"
                    yield self._get_spinner_hide_css(spinner_1_class)
                    spinner_2_class = f'connect-2-{randint(100, 999)}'
                    yield self._get_spinner_content_dict(spinner_2_class)

                    try:
                        remote_python = RemotePython(activity)
                        await remote_python.start()
                        self.connected_at = datetime.now()
                        break
                    except Exception:
                        yield self._get_spinner_hide_css(spinner_2_class)
                        yield "failed.\n"
                        asyncio.create_task(activity.parent.terminate())

                # TODO: It still doesn't fix the problem.
                #  Looks like there's something more on the provider that needs awaiting
                await remote_python.wait_for_remote_kernel()

                #  Staying with timeout for now
                await asyncio.sleep(10)
        except asyncio.TimeoutError:
            yield self._get_spinner_hide_css(spinner_1_class)
            if 'spinner_2_class' in locals():
                yield self._get_spinner_hide_css(spinner_2_class)
            yield "\nReached timeout."
        else:
            yield self._get_spinner_hide_css(spinner_2_class)
            yield "Ready."
            self._remote_python = remote_python

    async def _get_activity(self, payload, offer_scorer=None):
        demand = await self._golem_node.create_demand(payload, allocations=[self._allocation], autostart=True)

        chain = Chain(
            demand.initial_proposals(),
            # offer_scorer,
            Map(negotiate),
            Map(default_create_agreement),
            Map(default_create_activity),
            Buffer(size=1),
        )
        async for activity in chain:
            yield activity

    async def _disconnect_and_pay(self):
        """Terminate agreement, wait max 5s for invoice, accept it, return accepted amount."""

        agreement = self._remote_python.activity.parent
        self._remote_python = None

        await agreement.close_all()

        stop = datetime.now() + timedelta(seconds=5)
        while datetime.now() < stop:
            if agreement.invoice is not None:
                break
            else:
                await asyncio.sleep(0.1)

        if agreement.invoice is None:
            return None

        await agreement.invoice.accept_full(self._allocation)
        await self._allocation.get_data(force=True)

        return float(agreement.invoice.data.amount)

    async def _get_kernel_image_details(self):
        async with aiohttp.ClientSession() as session:
            registry_info_url = f'https://registry.golem.network/v1/image/info?tag={KERNEL_IMAGE_TAG}&count=true'
            try:
                async with session.get(registry_info_url, raise_for_status=True) as resp:
                    return await resp.json()
            except aiohttp.ClientResponseError:
                raise

    async def _parse_connect_args(self, text, image_details):
        """IN: raw text passed to connect. OUT: payload (or raises exception)."""

        manifest = open(Path(__file__).parent.joinpath("manifest.json"), "rb").read()
        manifest = (manifest
                    .decode('utf-8')
                    .replace('{sha3}', image_details['sha3'])
                    .replace('{image_url}', image_details['http']))
        manifest = base64.b64encode(manifest.encode('utf-8')).decode("utf-8")

        params = {
            "manifest": manifest,
            "capabilities": ['vpn', 'inet', 'manifest-support'],
            "min_mem_gib": 0,
            "min_cpu_threads": 0,
            "min_storage_gib": 0,
        }
        strategy = DEFAULT_SCORING_STRATEGY
        connection_timeout = DEFAULT_CONNECTION_TIMEOUT

        parts = text.split()
        for part in parts:
            # if part.startswith("image_hash="):
            #     params["image_hash"] = part[11:]
            if part.startswith("mem>"):
                params["min_mem_gib"] = float(part[4:])
            elif part.startswith("cores>"):
                params["min_cpu_threads"] = int(part[6:])
            elif part.startswith("disk>"):
                params["min_storage_gib"] = float(part[5:])
            elif part.startswith("timeout="):
                parsed_seconds = parse_to_seconds(part[8:])
                if parsed_seconds is None:
                    raise ValueError(f"Unknown timeout format {part[8:]}")
                else:
                    connection_timeout = timedelta(seconds=parsed_seconds)
            # elif part.startswith("strategy="):
            #     strategy = part[9:]
            #     if strategy not in STRATEGY_SCORING_FUNCTION:
            #         raise ValueError(f"Unknown strategy {part[9:]}")
            # elif part.startswith("cuda="):
            #     if part[5:].strip().lower() in {'yes', 'y', '1', 'true'}:
            #         params["capabilities"].append('cuda')
            else:
                raise ValueError(f"Unknown option: {part}")

        scoring_function = STRATEGY_SCORING_FUNCTION[strategy]
        # Scorer not available in current golem_core library version
        # offer_scorer = SimpleScorer(scoring_function, min_proposals=10, max_wait=timedelta(seconds=3))
        offer_scorer = None
        payload = ManifestVmPayload(**params)
        return payload, offer_scorer, connection_timeout

    ########################################################
    #   Functions that change nothing, just return some text
    def _get_status_text(self):
        app_key = self._get_or_create_yagna_appkey()
        if app_key is None:
            app_key = GolemNode().app_key
        id_data = json.loads(check_output(["yagna", "app-key", "list", "--json"]))

        for el in id_data:
            if el["key"] == app_key:
                node_id = el["id"]
                break
        else:
            node_id = "[unknown node id]"  # this is possible when user set YAGNA_APPKEY to not existing value

        connection_status = 'Established' if self.connected else 'Disconnected'
        activity = self._remote_python.activity if self.connected else None
        provider_info = self._provider_info_text(activity) if self.connected else ''
        connection_time = self._get_connection_time()
        connection_time_str = f'Connection time: {connection_time}' if self.connected else ''

        return STATUS_TEMPLATE.format(
            node_id=node_id,
            connection_status=connection_status,
            # budget=self._get_budget_text(),
            polygon_status=self._get_network_status_text('polygon'),
            goerli_status=self._get_network_status_text('goerli'),
            provider_info=provider_info,
            connection_time=connection_time_str,
        )

    def _get_or_create_yagna_appkey(self):
        if os.getenv('YAGNA_APPKEY') is None:
            id_data = json.loads(check_output(["yagna", "app-key", "list", "--json"]))
            yagna_jupter_app = next((app for app in id_data if app['name'] == YAGNA_APPNAME_JUPYTER), None)
            if yagna_jupter_app is None:
                return check_output(["yagna", "app-key", "create", YAGNA_APPNAME_JUPYTER]).decode('utf-8').strip('"\n')
            else:
                return yagna_jupter_app['key']
        else:
            return os.getenv('YAGNA_APPKEY')

    def _get_connection_time(self):
        return humanize.naturaldelta(datetime.now() - self.connected_at) if self.connected else ''

    def _get_help_text(self):
        return HELP_TEMPLATE

    def _get_network_status_text(self, network):
        if network == 'polygon':
            network_full_name = 'Polygon[mainnet]'
        elif network == 'goerli':
            network_full_name = 'Goerli[testnet]'
        else:
            network_full_name = network

        template = 'On {network_full_name}: {glm:.2f} {curr} {gas:.4f} {gas_curr}'
        data = json.loads(check_output(["yagna", "payment", "status", "--json", "--network", network]))

        return template.format(
            network_full_name=network_full_name,
            glm=float(data["amount"]),
            curr=data["token"],
            gas=float(data["gas"]["balance"]),
            gas_curr=data["gas"]["currency_short_name"],
        )

    def _get_budget_text(self):
        if self._allocation is None:
            return "No budget defined!"

        amount = self._allocation.data.remaining_amount
        payment_platform = self._allocation.data.payment_platform
        network, currency = payment_platform.split('-')[1:]

        return f"Allocated {amount} {currency} on {network}"

    def _provider_info_text(self, activity):
        proposal_data = activity.parent.parent.data
        properties = proposal_data.properties

        # cuda_card = next((cap.split(',', 1)[1].strip()
        #                   for cap in properties['golem.runtime.capabilities']
        #                   if cap.startswith('cuda,')),
        #                  None)
        # gpu = cuda_card if cuda_card else 'None'

        return PROVIDER_TEMPLATE.format(
            provider_id=proposal_data.issuer_id,
            provider_name=properties['golem.node.id.name'],
            cpu=properties['golem.inf.cpu.cores'],
            ram=properties['golem.inf.mem.gib'],
            disk=properties['golem.inf.storage.gib'],
            # gpu=gpu,
        )

    def _payload_text(self, payload):
        mem = payload.min_mem_gib
        disk = payload.min_storage_gib
        cores = payload.min_cpu_threads
        # cuda = 'cuda' in payload.capabilities

        constraint_parts = []
        if mem:
            constraint_parts.append(f"RAM>={mem}gb")
        if disk:
            constraint_parts.append(f"DISK>={disk}gb")
        if cores:
            constraint_parts.append(f"CPU>={cores}")
        # if cuda:
        #     constraint_parts.append("CUDA=yes")

        if constraint_parts:
            return "(" + " ".join(constraint_parts) + ")"
        else:
            return "just any machine"
