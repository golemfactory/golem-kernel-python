import asyncio
import websockets
from urllib.parse import urlparse
import json

from golem_core import commands


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

            commands.SendFile('provider/server.py', '/ttt/server.py'),
            commands.Run('cp /ttt/server.py /python_server/server.py'),

            commands.Run('nohup python server.py > /dev/null 2>&1 &'),
        )
        #   NOTE: We don't set any timeout here because caller of RemotePython.start() should
        #         have their own timeout either way.
        await batch.wait()

        #   Wait a little while until server.py starts.
        #   TODO: a better solution maybe?
        await asyncio.sleep(3)

        url = network.node._api_config.net_url
        net_api_ws = urlparse(url)._replace(scheme="ws").geturl()
        self._connection_uri = f"{net_api_ws}/net/{network.id}/tcp/{ip}/5000"
        self._auth_header = {"Authorization": f"Bearer {self.activity.node._api_config.app_key}"}
        self._ws = await websockets.connect(self._connection_uri, extra_headers=self._auth_header)

    async def execute(self, code):
        if self._ws is None:
            raise RuntimeError("RemotePython didn't start succesfully")

        data = code.encode()
        bytes_len = len(data)
        full_data = str(bytes_len).encode() + b' ' + data
        await self._ws.send(full_data)
        response = await self._receive()
        return json.loads(response.decode())

    async def _receive(self):
        init_data = await self._ws.recv()

        message_len, data = init_data.split(b' ', maxsplit=1)
        message_len = int(message_len.decode())

        while len(data) < message_len:
            data += await self._ws.recv()

        with open("ttt.txt", "ab+") as f:
            f.write(data + b"\n\n\n")

        return data
