import asyncio
import aiofiles

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

    async def execute(self, code):
        await log("EXECUTE", code)
        remote_python = await self.remote_python()
        output = await remote_python.execute(code)
        await log("RESULT", output)
        return output

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
