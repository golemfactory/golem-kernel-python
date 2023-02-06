import asyncio
import websockets

async def hello():
    async with websockets.connect("ws://127.0.0.1:5000") as websocket:
        for i in range(10):
            code = "a=7\nprint(a + 3)\na"
            await websocket.send(code)
            print(await websocket.recv())

asyncio.run(hello())
