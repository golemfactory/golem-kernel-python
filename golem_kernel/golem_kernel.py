from ipykernel.kernelbase import Kernel

from .golem import Golem

import logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


import comm
from .comm.comm import BaseComm
from .comm.manager import CommManager
import threading
import typing as t
from traitlets import HasTraits


def _create_comm(*args, **kwargs):
    """Create a new Comm."""
    return BaseComm(*args, **kwargs)


# there can only be one comm manager in a ipykernel process
_comm_lock = threading.Lock()
_comm_manager: t.Optional[CommManager] = None


def _get_comm_manager(*args, **kwargs):
    """Create a new CommManager."""
    global _comm_manager  # noqa
    if _comm_manager is None:
        with _comm_lock:
            if _comm_manager is None:
                _comm_manager = CommManager(*args, **kwargs)
    return _comm_manager


comm.create_comm = _create_comm
comm.get_comm_manager = _get_comm_manager


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

        self.comm_manager = comm.get_comm_manager()

        assert isinstance(self.comm_manager, HasTraits)
        # self.shell.configurables.append(self.comm_manager)
        comm_msg_types = ["comm_open", "comm_msg", "comm_close"]
        for msg_type in comm_msg_types:
            self.shell_handlers[msg_type] = getattr(self.comm_manager, msg_type)

    async def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        async for content, is_result in self._golem.execute(code):

            logger.info(f'-----Got return message (result: {is_result}, silent: {silent}): {content}')

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
