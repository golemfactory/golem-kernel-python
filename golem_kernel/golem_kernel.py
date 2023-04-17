from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from urllib.parse import parse_qs

from ipykernel.kernelbase import Kernel

from .golem import Golem


class GoogleAuthHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        code = parse_qs(parsed.query)['code'][0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(f"Code: {code}", "utf-8"))


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

        # self.http_server = ThreadingHTTPServer(('127.0.0.1', 9000), GoogleAuthHandler)
        # self.http_server.serve_forever()
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
        # self.http_server.shutdown()
        await self._golem.aclose()
