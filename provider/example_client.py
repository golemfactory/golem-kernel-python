import asyncio
import websockets

async def hello():
    async with websockets.connect("ws://localhost:5000") as websocket:
        for i in range(10):
            code = f"a={i}\nprint(a)\na"
            await websocket.send(code)
            print(await websocket.recv())

asyncio.run(hello())
