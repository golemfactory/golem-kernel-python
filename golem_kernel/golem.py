import asyncio
import aiofiles

from golem_core import GolemNode, Payload
from golem_core.mid import (
    Chain, Map, Buffer,
    default_negotiate, default_create_agreement, default_create_activity
)

from .remote_python import RemotePython

PAYLOAD = Payload.from_image_hash("f27375a678d22d6fb323026a08e8a0d1249a9edbff7236a0fa4c236b")

async def log(*data):
    line = " ".join(data) + "\n"
    async with aiofiles.open("kernel.log", mode='a+') as f:
        await f.write(line)

class Golem:
    def __init__(self):
        self._create_remote_python_lock = asyncio.Lock()
        self._golem_node = None
        self._remote_python = None

    async def execute(self, code):
        await log("EXECUTE", code)
        remote_python = await self.remote_python()
        return await remote_python.execute(code)

    async def aclose(self):
        await log("shutdown start")
        await asyncio.sleep(2)
        await log("stopped")

    async def remote_python(self):
        async with self._create_remote_python_lock:
            if self._remote_python is None:
                self._remote_python = await self._create_remote_python()
        return self._remote_python

    async def _create_remote_python(self):
        self._golem_node = GolemNode()
        await self._golem_node.start()
        activity = await self._get_activity()
        remote_python = RemotePython(activity)
        await remote_python.start()
        return remote_python

    async def _get_activity(self):
        golem = self._golem_node

        allocation = await golem.create_allocation(1)
        demand = await golem.create_demand(PAYLOAD, allocations=[allocation])

        chain = Chain(
            demand.initial_proposals(),
            Map(default_negotiate),
            Map(default_create_agreement),
            Map(default_create_activity),
            Buffer(size=1),
        )
        return await chain.__anext__()
