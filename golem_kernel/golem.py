import asyncio
import aiofiles

from golem_core import GolemNode

async def log(*data):
    line = " ".join(data) + "\n"
    async with aiofiles.open("kernel.log", mode='a+') as f:
        await f.write(line)

class Golem:
    def __init__(self):
        self._get_remote_python_lock = asyncio.Lock()
        self._golem_node = None
        self._remote_python = None

    async def execute(self, code):
        await log("EXECUTE", code)
        remote_python = await self.remote_python()
        return await remote_python.execute(code)

    async def remote_python(self):
        async with self._get_remote_python_lock:
            if self._remote_python is None:
                self._remote_python = await self._get_remote_python()
        return self._remote_python

    async def _get_remote_python(self):
        node = GolemNode()
        await node.start()

        class X:
            async def start(self):
                return 'started'

            async def execute(self, input_):
                return f'executed 2 {input_}'

        remote_python = X()
        return remote_python

    async def aclose(self):
        await log("shutdown start")
        await asyncio.sleep(2)
        await log("stopped")
