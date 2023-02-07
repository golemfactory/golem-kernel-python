import websockets

from golem_core import commands

from urllib.parse import urlparse

class RemotePython:
    def __init__(self, activity, *, start_timeout=300, batch_timeout=300):
        self.activity = activity
        self.start_timeout = start_timeout
        self.batch_timeout = batch_timeout

        self._connection_uri = None
        self._auth_header = None
        self._ws = None

    async def start(self):
        network = await self.activity.node.create_network("192.168.0.1/24")
        provider_id = self.activity.parent.parent.data.issuer_id
        ip = await network.create_node(provider_id)
        deploy_args = {"net": [network.deploy_args(ip)]}

        batch = await self.activity.execute_commands(
            commands.Deploy(deploy_args),
            commands.Start(),

            commands.SendFile('provider/server.py', '/ttt/server.py'),
            commands.SendFile('provider/local_client.py', '/ttt/local_client.py'),
            commands.Run('cp /ttt/server.py /python_server/server.py'),
            commands.Run('cp /ttt/local_client.py /python_server/local_client.py'),

            commands.Run('nohup python server.py > /dev/null 2>&1 &'),
        )
        try:
            await batch.wait(timeout=100)
        except Exception:
            print(batch.events)
            raise

        print("STARTED")

        #   IMPORTANT: wait until the service starts
        #   (FIXME: better implementation)
        import asyncio
        await asyncio.sleep(3)

        batch = await self.activity.execute_commands(
            commands.Run('python local_client.py'),
        )
        try:
            await batch.wait(timeout=10)
        finally:
            print(batch.events)

        url = network.node._api_config.net_url
        net_api_ws = urlparse(url)._replace(scheme="ws").geturl()
        self._connection_uri = f"{net_api_ws}/net/{network.id}/tcp/{ip}/5000"
        self._auth_header = {"Authorization": f"Bearer {self.activity.node._api_config.app_key}"}
        self._ws = await websockets.connect(self._connection_uri, extra_headers=self._auth_header)

    async def execute(self, code):
        await self._ws.send(code.encode())
        return (await self._ws.recv()).decode()
