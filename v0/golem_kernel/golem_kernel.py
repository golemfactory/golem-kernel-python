import asyncio

from ipykernel.kernelbase import Kernel

class GolemKernel(Kernel):
    implementation = 'GLMKernel'
    implementation_version = '0.001'
    language = 'python'
    language_version = '3'
    language_info = {
        'name': 'python',
        'mimetype': 'text/x-python',
        'file_extension': '.py',
    }
    banner = "GLM Kernel - your python lives in the Golem Network"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._golem_data = {
            "get_remote_python_lock": asyncio.Lock(),
            "remote_python": None,
        }

    @property
    def g(self):
        return self._golem_data

    async def remote_python(self):
        async with self.g["get_remote_python_lock"]:
            if self.g["remote_python"] is None:
                self.g["remote_python"] = await self._get_remote_python()
        return self.g["remote_python"]

    async def _get_remote_python(self):
        class X:
            async def start(self):
                return 'started'

            async def execute(self, input_):
                return f'executed {input_}'

        remote_python = X()
        return remote_python

    async def do_execute(
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=False
    ):

        remote_python = await self.remote_python()
        result = await remote_python.execute(code)

        if not silent:
            stream_content = {'name': 'stdout', 'text': result}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }
