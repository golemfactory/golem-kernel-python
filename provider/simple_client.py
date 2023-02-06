from collections import defaultdict
from queue import Empty
from time import sleep

from jupyter_client.blocking import BlockingKernelClient


class SimpleClient:
    """POC of a client talking to a kernel.

    Important note: this is **strictly** a POC. We (probably?) should not be improving this
    implementation, but instead:
    * either pass messages directly to the requestor-side kernel (and maybe do some processing there)
    * or decide what do we exactly need (e.g. stdout streaming) and modify the interface
    """

    def __init__(self, connection_file_name):
        self.kc = BlockingKernelClient(connection_file=connection_file_name)

        self.kc.load_connection_file()
        self.kc.start_channels()

    def execute(self, code):
        """Execute code. Get stdout and result, if any."""

        self.kc.execute(code)
        data = defaultdict(str)
        while True:
            try:
                reply = self.kc.get_iopub_msg(timeout=1)
            except Empty:
                sleep(0.1)
                continue

            finished, reply_data = self._parse_msg(reply)
            for key, val in reply_data.items():
                data[key] += val
            if finished:
                return data

    def _parse_msg(self, msg):
        data = {}
        finished = False
        type_, content = msg['msg_type'], msg['content']
        if type_ == 'stream':
            data['stdout'] = content['text']
        elif type_ == 'error':
            data['stdout'] = "\n".join(content['traceback'])
        elif type_ == 'execute_result':
            data['result'] = content['data']['text/plain']
        elif type_ == 'status' and content['execution_state'] == 'idle':
            finished = True

        return finished, data
