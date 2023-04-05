from ipykernel.kernelbase import Kernel

from .golem import Golem

class GolemKernel(Kernel):
    implementation = 'GolemKernel'
    implementation_version = '0.001'
    language = 'python'
    language_version = '3'
    language_info = {
        'name': 'python',
        'mimetype': 'text/x-python',
        'file_extension': '.py',
    }
    banner = "Golem Kernel - your python lives in the Golem Network"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._golem = Golem()

    async def do_execute(
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=False
    ):
        async for content, is_result in self._golem.execute(code):
            if silent:
                continue

            if is_result:
                if content['type'] == 'display_data':
                    display_data_content = {
                        'data': content['content'],
                        'metadata': {},  # this is necessary for jupyterlab, but not jupyter notebook
                    }
                    self.send_response(self.iopub_socket, 'display_data', display_data_content)
                elif content['type'] == 'execute_result':
                    execute_result_content = {
                        'data': {'text/plain': content['content']},
                        'execution_count': self.execution_count,
                        'metadata': {},  # this is necessary for jupyterlab, but not jupyter notebook
                    }
                    self.send_response(self.iopub_socket, 'execute_result', execute_result_content)
            else:
                stream_content = {'name': 'stdout', 'text': content}
                self.send_response(self.iopub_socket, 'stream', stream_content)

        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    async def do_shutdown(self, restart):
        await self._golem.aclose()
