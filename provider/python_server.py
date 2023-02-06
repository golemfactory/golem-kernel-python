import subprocess
import asyncio
import websockets
import json

from simple_client import SimpleClient

def start_kernel():
    cmd = ["jupyter", "kernel", "--kernel", "python3"]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)

    proc.stderr.readline()
    line = proc.stderr.readline()
    connection_file_name = line.decode().strip().split()[3]
    return connection_file_name


async def main():
    # connection_file_name = start_kernel()
    # client = SimpleClient(connection_file_name)

    # async def python_server(websocket):
    #     async for code in websocket:
    #         result = client.execute(code)
    #         await websocket.send(json.dumps(result))

    async def python_server(websocket):
        async for msg in websocket:
            await websocket.send(msg)

    async with websockets.serve(python_server, "0.0.0.0", 5000):
        await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())
