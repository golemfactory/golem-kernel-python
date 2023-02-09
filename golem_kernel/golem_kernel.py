from ipykernel.kernelbase import Kernel

from .golem import Golem

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

        self._golem = Golem()

    async def do_execute(
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=False
    ):
        output = await self._golem.execute(code)

        if not silent:
            if 'stdout' in output:
                stream_content = {'name': 'stdout', 'text': output['stdout']}
                self.send_response(self.iopub_socket, 'stream', stream_content)
            if 'result' in output:
                execute_result_content = {
                    'data': {'text/plain': output['result']},
                    'execution_count': self.execution_count,
                    'metadata': {},  # this is necessary for jupyterlab, but not jupyter notebook
                }
                self.send_response(self.iopub_socket, 'execute_result', execute_result_content)

        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    async def do_shutdown(self, restart):
        await self._golem.aclose()
