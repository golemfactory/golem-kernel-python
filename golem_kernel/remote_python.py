from pathlib import Path
import websockets
from urllib.parse import urlparse
import json
import pprint

from golem_core.core.activity_api import commands


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
            commands.Run('/sbin/ifconfig eth1 mtu 1500 up'),
            commands.Run('cp -R /usr/src/app/venv /usr/src/app/output/venv'),
            commands.Run('echo "142.250.75.13    accounts.google.com" >> /etc/hosts'),
            commands.Run('echo "142.250.203.196    googleapis.com" >> /etc/hosts'),
            commands.Run('echo "142.250.186.202    oauth2.googleapis.com" >> /etc/hosts'),
        )
        #   NOTE: We don't set any timeout here because caller of RemotePython.start() should
        #         have their own timeout either way.
        await batch.wait()

        batch = await self.activity.execute_commands(
            commands.Run("sed -i 's=/usr/src/app/venv=/usr/src/app/output/venv=g' /usr/src/app/output/venv/bin/*"),
        )
        await batch.wait()

        batch = await self.activity.execute_commands(
            commands.Run('nohup /usr/src/app/output/venv/bin/python3 server.py > /usr/src/app/output/out.txt 2>&1 &'),
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

    async def execute(self, code):
        if self._ws is None:
            raise RuntimeError("RemotePython didn't start successfully")

        await self._send(code)
        with open('out.txt', 'a') as f:
            f.write(f'-----AFTER SEND COMMAND TO REMOTE KERNEL-----sent: {str(code)}')
        response = await self._receive()
        with open('out.txt', 'a') as f:
            f.write(f'resp: {str(response)}')
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
        with open('out.txt', 'a') as f:
            pprint.pprint(init_data, f)

        message_len, data = init_data.split(b' ', maxsplit=1)
        message_len = int(message_len.decode())

        while len(data) < message_len:
            data_incr = await self._ws.recv()

            with open('out.txt', 'a') as f:
                pprint.pprint(data_incr, f)

            data += data_incr

        return data

    async def upload_file(self, local_path):
        batch = await self.activity.execute_commands(
            commands.SendFile(local_path, f"/usr/src/app/output/{Path(local_path).name}"),
        )
        await batch.wait()

    async def download_file(self, remote_file):
        batch = await self.activity.execute_commands(
            commands.DownloadFile(f"/usr/src/app/output/{remote_file}", remote_file),
        )
        await batch.wait()
