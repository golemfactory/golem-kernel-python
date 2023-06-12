from pathlib import Path
import websockets
from urllib.parse import urlparse
import json
import pprint

from golem_core.core.activity_api import commands

from . import WORKDIR_PATH


import logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class RemotePython:
    def __init__(self, activity):
        self.activity = activity

        self._connection_uri = None
        self._auth_header = None
        self._ws = None

    async def start(self):
        activity = self.activity

        network = await activity.node.create_network("192.168.0.1/24")
        provider_id = activity.parent.parent.data.issuer_id
        ip = await network.create_node(provider_id)
        deploy_args = {"net": [network.deploy_args(ip)]}

        batch = await self.activity.execute_commands(
            commands.Deploy(deploy_args),
            commands.Start(),
            commands.Run('/sbin/ifconfig eth1 mtu 1450 up'),
            commands.Run(f'cp -R /usr/src/app/venv {WORKDIR_PATH}venv'),
            commands.Run('echo "142.250.75.13    accounts.google.com" >> /etc/hosts'),
            commands.Run('echo "142.250.203.196    googleapis.com" >> /etc/hosts'),
            commands.Run('echo "142.250.186.202    oauth2.googleapis.com" >> /etc/hosts'),
        )
        #   NOTE: We don't set any timeout here because caller of RemotePython.start() should
        #         have their own timeout either way.
        await batch.wait()

        batch = await self.activity.execute_commands(
            commands.Run(f"sed -i 's=/usr/src/app/venv={WORKDIR_PATH}venv=g' {WORKDIR_PATH}venv/bin/*"),
        )
        await batch.wait()

        batch = await self.activity.execute_commands(
            commands.Run(f'nohup {WORKDIR_PATH}venv/bin/python3 server.py > {WORKDIR_PATH}out.txt 2>&1 &'),
        )
        await batch.wait()

        batch = await self.activity.execute_commands(
            commands.Run('/usr/src/app/wait_for_server.sh'),
        )
        await batch.wait()

        url = network.node._api_config.net_url
        net_api_ws = urlparse(url)._replace(scheme="ws").geturl()
        self._connection_uri = f"{net_api_ws}/net/{network.id}/tcp/{ip}/5000"
        self._auth_header = {"Authorization": f"Bearer {self.activity.node._api_config.app_key}"}
        self._ws = await websockets.connect(self._connection_uri, extra_headers=self._auth_header, ping_timeout=None,
                                            max_size=5_000_000)

    async def wait_for_remote_kernel(self):
        batch = await self.activity.execute_commands(commands.Run('/usr/src/app/wait_for_kernel.sh'))
        await batch.wait()
        logger.info('-----KERNEL SHOULD BE READY-----')

    async def execute(self, code):
        if self._ws is None:
            raise RuntimeError("RemotePython didn't start successfully")

        await self._send(code)
        logger.info(f'-----AFTER SEND COMMAND TO REMOTE KERNEL-----sent: {str(code)}')
        response = await self._receive()
        logger.info(f'-----RESPONSE: {str(response)}')
        return json.loads(response.decode())

    async def _send(self, code):
        data = code.encode()
        bytes_len = len(data)
        full_data = str(bytes_len).encode() + b' ' + data
        await self._ws.send(full_data)

    async def _receive(self):
        #   NOTE: We always send a single message and receive a single response, so this simplified
        #         implementation should be OK - we never receive anything after the message_len.
        init_data = await self._ws.recv()
        logger.info(pprint.pformat(init_data))

        message_len, data = init_data.split(b' ', maxsplit=1)
        message_len = int(message_len.decode())

        while len(data) < message_len:
            data_incr = await self._ws.recv()

            logger.info(pprint.pformat(data_incr))

            data += data_incr

        return data

    async def upload_file(self, local_path):
        batch = await self.activity.execute_commands(
            commands.SendFile(local_path, f"{WORKDIR_PATH}{Path(local_path).name}"),
        )
        await batch.wait()

    async def download_file(self, remote_file):
        batch = await self.activity.execute_commands(
            commands.DownloadFile(f"{WORKDIR_PATH}{remote_file}", remote_file),
        )
        await batch.wait()
