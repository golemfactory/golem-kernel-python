import asyncio
import base64
from datetime import datetime, timedelta
import json
from pathlib import Path
from random import random
from subprocess import check_output, check_call

import async_timeout
from golem_core.core.golem_node import GolemNode
from golem_core.pipeline import Chain, Map, Buffer
from golem_core.core.market_api import ManifestVmPayload
from golem_core.core.market_api.pipeline import default_negotiate, default_create_agreement, default_create_activity
import humanize
from pytimeparse import parse as parse_to_seconds

from .remote_python import RemotePython
from . import TMPDIR_PATH


import logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


SPINNER_SVG = '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/><path d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z"><animateTransform attributeName="transform" type="rotate" dur="0.75s" values="0 12 12;360 12 12" repeatCount="indefinite"/></path></svg>'

STATUS_TEMPLATE = '''\
My node ID: {node_id}
My wallet address: {node_id}
{polygon_status}
{rinkeby_status}
Connection status: {connection_status}
{provider_info}{connection_time}
'''

HELP_TEMPLATE = '''\
     _                   _                             ____       _                
    | |_   _ _ __  _   _| |_ ___ _ __    ___  _ __    / ___| ___ | | ___ _ __ ___  
 _  | | | | | '_ \| | | | __/ _ \ '__|  / _ \| '_ \  | |  _ / _ \| |/ _ \ '_ ` _ \ 
| |_| | |_| | |_) | |_| | ||  __/ |    | (_) | | | | | |_| | (_) | |  __/ | | | | |
 \___/ \__,_| .__/ \__, |\__\___|_|     \___/|_| |_|  \____|\___/|_|\___|_| |_| |_| version: 0.1.0
            |_|    |___/                                                           

Easy to use tool to run Your Jupyter Notebooks on the Golem Network!

COMMANDS:    
    %status		Shows current status of Jupyter on Golem
    %fund		Requests for testnet funds, e.g. '%fund rinkeby'
    %budget		Allocates GLM tokens for payments, e.g. '%budget rinkeby 2'
    %connect		Looks for Provider which meets with defined criteria [mem|cores|disk|cuda], e.g. '%connect mem>1'				
    %disconnect 	Disconnects from the currently active Provider
    %download	 	Downloads file from Provider's ./workdir folder to local machine, e.g. '%download dataset.csv'
    %upload		Uploads file from local machine into Provider's ./workdir folder, e.g. '%upload results.csv'
    %help		Shows this message
'''

PROVIDER_TEMPLATE = '''\
Connected to {provider_name} [{provider_id}]
    RAM: {ram} GB
    DISK: {disk} GB
    CPU: {cpu} cores
    GPU: {gpu}
'''


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
DEFAULT_CONNECTION_TIMEOUT = timedelta(minutes=5)


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
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                yield f"Error running a local command: {e}, {tb}", False
        elif not self.connected:
            yield f"Provider not connected. Available commands: {', '.join(local_commands)}.", False
        else:
            async for out in self._alter_and_run_remote_command(code):
                yield out

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
    async def _run_local_command(self, code):
        if code == '%status':
            yield self._get_status_text()
        elif code == '%help':
            yield self._get_help_text()
        elif code.startswith('%fund'):
            network = code.split()[1]
            yield "Waiting for funds\n"
            try:
                self._get_funds(network)
            except Exception:
                yield "Funding failed"
            else:
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

                payload, offer_scorer, timeout = await self._parse_connect_args(args_str)
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
            code = f'{code} --build {TMPDIR_PATH} --no-cache-dir'
            yield {
                "type": "display_data",
                "content": {
                    "text/plain": "<IPython.core.display.HTML object>",
                    "text/html": SPINNER_SVG,
                }
            }, False
            async for content, is_result in self._run_remote_command(code):
                if not is_result:
                    yield {"type": "clear_output"}, False
                yield content, is_result
        else:
            async for out in self._run_remote_command(code):
                yield out

    async def _run_remote_command(self, code):
        result = await self._remote_python.execute(code)
        if "stdout" in result:
            yield result["stdout"], False
        if "result" in result:
            yield result["result"], True

    def _get_funds(self, network):
        check_call(["yagna", "payment", "fund", "--network", network])

    async def _create_allocation(self, network, amount):
        if self._allocation is not None:
            await self._allocation.release()
            self._allocation = None

        async def on_event(event) -> None:
            logger.info(f'-----EVENT: {event}')

        if self._golem_node is None:
            self._loop = asyncio.get_running_loop()
            self._golem_node = GolemNode()
            self._golem_node.event_bus.listen(on_event)
            await self._golem_node.start()

        check_call(["yagna", "payment", "init", "--network", network])
        check_call(["yagna", "payment", "init", "--network", network, "--sender"])

        self._allocation = await self._golem_node.create_allocation(amount, network)
        await self._allocation.get_data()

    async def _connect(self, payload, offer_scorer, timeout):
        try:
            async with async_timeout.timeout(int(timeout.total_seconds())):
                yield f"Progress: 1/3\n" \
                      "    Demand created. Waiting for counter proposal.\n" \
                      f"    Searching for {self._payload_text(payload)}...\n" \
                      f"    Will try to connect for {humanize.naturaldelta(timeout)}.\n"
                async for activity in self._get_activity(payload, offer_scorer):
                    yield "Progress: 2/3\n" \
                          "    Agreement created.\n" \
                          f"    {self._provider_info_text(activity)}" \
                          "Progress: 3/3\n" \
                          "    Engine is starting. It might take few minutes...\n"
                    try:
                        remote_python = RemotePython(activity)
                        await remote_python.start()
                        self.connected_at = datetime.now()
                        break
                    except Exception:
                        yield "failed.\n"
                        asyncio.create_task(activity.parent.terminate())

                # TODO: It still doesn't fix the problem.
                #  Looks like there's something more on the provider that needs awaiting
                await remote_python.wait_for_remote_kernel()

                #  Staying with timeout for now
                await asyncio.sleep(10)
        except asyncio.TimeoutError:
            yield "\nReached timeout."
        else:
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
            logger.info(f'-----ACTIVITY YIELDED: {str(activity)}')
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

    async def _parse_connect_args(self, text):
        """IN: raw text passed to connect. OUT: payload (or raises exception)."""

        manifest = open(Path(__file__).parent.joinpath("manifest.json"), "rb").read()
        manifest = base64.b64encode(manifest).decode("utf-8")

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
            elif part.startswith("cuda="):
                if part[5:].strip().lower() in {'yes', 'y', '1', 'true'}:
                    params["capabilities"].append('cuda')
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
        id_data = json.loads(check_output(["yagna", "app-key", "list", "--json"]))

        app_key = GolemNode().app_key
        for el in id_data:
            if el["key"] == app_key:
                node_id = el["id"]
                break
        else:
            node_id = "[unknown node id]"  # this should not be possible

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
            rinkeby_status=self._get_network_status_text('rinkeby'),
            provider_info=provider_info,
            connection_time=connection_time_str,
        )

    def _get_connection_time(self):
        return humanize.naturaldelta(datetime.now() - self.connected_at) if self.connected else ''

    def _get_help_text(self):
        return HELP_TEMPLATE

    def _get_network_status_text(self, network):
        if network == 'polygon':
            network_full_name = 'Polygon[mainnet]'
        elif network == 'rinkeby':
            network_full_name = 'Rinkeby[testnet]'
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

        cuda_card = next((cap.split(',', 1)[1].strip()
                          for cap in properties['golem.runtime.capabilities']
                          if cap.startswith('cuda,')),
                         None)
        gpu = cuda_card if cuda_card else 'None'

        return PROVIDER_TEMPLATE.format(
            provider_id=proposal_data.issuer_id,
            provider_name=properties['golem.node.id.name'],
            cpu=properties['golem.inf.cpu.cores'],
            ram=properties['golem.inf.mem.gib'],
            disk=properties['golem.inf.storage.gib'],
            gpu=gpu,
        )

    def _payload_text(self, payload):
        mem = payload.min_mem_gib
        disk = payload.min_storage_gib
        cores = payload.min_cpu_threads
        cuda = 'cuda' in payload.capabilities

        constraint_parts = []
        if mem:
            constraint_parts.append(f"RAM>={mem}gb")
        if disk:
            constraint_parts.append(f"DISK>={disk}gb")
        if cores:
            constraint_parts.append(f"CPU>={cores}")
        if cuda:
            constraint_parts.append("CUDA=yes")

        if constraint_parts:
            return "(" + " ".join(constraint_parts) + ")"
        else:
            return "just any machine"
