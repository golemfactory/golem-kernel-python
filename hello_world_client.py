import asyncio
import websockets
import sys

url = sys.argv[1]

async def t1():
    headers = {"Authorization": "Bearer 6f945361959c4888b614e5b6b448d49d"}
    async with websockets.connect(url, extra_headers=headers) as websocket:
        for i in range(10):
            code = "a=7\nprint(a)\na + 4"
            await websocket.send(code.encode())
            print("Message sent, waiting ...")
            print(await websocket.recv())

asyncio.run(t1())
