from ipykernel.kernelbase import Kernel
import asyncio

class EchoKernel(Kernel):
    implementation = 'Echo'
    implementation_version = '1.0'
    language = 'no-op'
    language_version = '0.1'
    language_info = {
        'name': 'Any text',
        'mimetype': 'text/plain',
        'file_extension': '.txt',
    }
    banner = "Echo kernel - as useful as a parrot"

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


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=EchoKernel)
