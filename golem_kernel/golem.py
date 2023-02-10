import asyncio
import aiofiles
import json
from subprocess import check_output

from golem_core import GolemNode, Payload
from golem_core.mid import (
    Chain, Map, Buffer,
    default_negotiate, default_create_agreement, default_create_activity
)
from yapapi.payload import vm

from .remote_python import RemotePython


PAYLOAD = Payload.from_image_hash(
    "701d57c13726afaf15bf8d602ce0710fc6119d0192507a220cef48d8",
    capabilities=[vm.VM_CAPS_VPN],
)

STATUS_TEMPLATE = '''\
Connected as node {id_}
On Polygon[mainet]: {polygon_glm:.2f} GLM {polygon_gas:.4f} MATIC
On Rinkeby[testnet]: {rinkeby_glm:.2f} tGLM {rinkeby_gas:.4f} tETH.

{budget}
'''

async def negotiate(proposal):
    return await asyncio.wait_for(default_negotiate(proposal), timeout=5)

async def log(*data):
    line = " ".join([str(x) for x in data]) + "\n"
    async with aiofiles.open("kernel.log", mode='a+') as f:
        await f.write(line)

class Golem:
    def __init__(self):
        self._create_remote_python_lock = asyncio.Lock()
        self._golem_node = None
        self._remote_python = None
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
        await log("EXECUTE", code)

        if any(code.startswith(x) for x in ('%status', '%fund', '%budget', '%connect')):
            try:
                async for out in self._run_local_command(code):
                    yield out
            except Exception as e:
                yield f"Error running a local command: {e}", False
        elif not self.connected:
            yield "Provider not connected", False
        else:
            async for out in self._run_remote_command(code):
                yield out

    async def aclose(self):
        await log("aclose")
        #   NOTE: We don't wait for invoices here.
        #         We could easily use golem_core.default_payment_manager.DefaultPaymentManager,
        #         but this doesn't make much sense now - payments/invoices require some separate solution.
        if self._golem_node is not None:
            #   Q: Why this?
            #   A: Current running loop is different than the loop that was running when GolemNode
            #      was started. We must use the latter to stop the GolemNode.
            fut = asyncio.run_coroutine_threadsafe(self._golem_node.aclose(), self._loop)
            fut.result()

    ##############
    #   LOCAL PART
    async def _run_local_command(self, code):
        if code == '%status':
            yield self._get_status_text(), False
        else:
            raise ValueError(f"Unknown command: {code}")

    def _get_status_text(self):
        id_data = json.loads(check_output(["yagna", "app-key", "list", "--json"]))
        rinkeby_data = json.loads(check_output(["yagna", "payment", "status", "--json", "--network", "rinkeby"]))
        polygon_data = json.loads(check_output(["yagna", "payment", "status", "--json", "--network", "polygon"]))

        app_key = GolemNode().app_key
        for el in id_data:
            if el["key"] == app_key:
                id_ = el["id"]
                break
        else:
            id_ = "[unknown node id]"  # this should not be possible

        status_data = {
            "id_": id_,
            "rinkeby_glm": float(rinkeby_data["amount"]),
            "rinkeby_gas": float(rinkeby_data["gas"]["balance"]),
            "polygon_glm": float(polygon_data["amount"]),
            "polygon_gas": float(polygon_data["gas"]["balance"]),
            "budget": self._get_budget_text(),
        }

        return STATUS_TEMPLATE.format(**status_data)

    def _get_budget_text(self):
        return "ZZZ"

    ###############
    #   REMOTE PART
    async def _run_remote_command(self, code):
        # yield "NO STDOUT", False
        # yield "NO RESULT", True
        # return

        remote_python = await self.remote_python()
        result = await remote_python.execute(code)
        if "stdout" in result:
            yield result["stdout"], False
        if "result" in result:
            yield result["result"], True

    async def remote_python(self):
        async with self._create_remote_python_lock:
            if self._remote_python is None:
                self._remote_python = await self._create_remote_python()
        return self._remote_python

    async def _create_remote_python(self):
        self._loop = asyncio.get_running_loop()
        self._golem_node = GolemNode()
        await self._golem_node.start()

        activity_cnt = 0
        async for activity in self._get_activity():
            activity_cnt += 1
            await log(activity)
            remote_python = RemotePython(activity)
            try:
                await asyncio.wait_for(remote_python.start(), timeout=100)
                await log("CREATED REMOTE PYTHON")
                return remote_python
            except Exception as e:
                await log("Startup failed", activity, e)
                import traceback
                await log(traceback.format_exc())

            #   FIXME
            if activity_cnt > 2:
                raise Exception("Failed to create a remote python")

    async def _get_activity(self):
        golem = self._golem_node

        allocation = await golem.create_allocation(1)
        demand = await golem.create_demand(PAYLOAD, allocations=[allocation])

        chain = Chain(
            demand.initial_proposals(),
            Map(negotiate),
            Map(default_create_agreement),
            Map(default_create_activity),
            Buffer(size=1),
        )
        async for activity in chain:
            yield activity
