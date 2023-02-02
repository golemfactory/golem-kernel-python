import asyncio

class Golem:
    def __init__(self):
        self._get_remote_python_lock = asyncio.Lock()
        self._remote_python = None

    async def execute(self, code):
        remote_python = await self.remote_python()
        return await remote_python.execute(code)

    async def remote_python(self):
        async with self._get_remote_python_lock:
            if self._remote_python is None:
                self._remote_python = await self._get_remote_python()
        return self._remote_python

    async def _get_remote_python(self):
        class X:
            async def start(self):
                return 'started'

            async def execute(self, input_):
                return f'executed 2 {input_}'

        remote_python = X()
        return remote_python
