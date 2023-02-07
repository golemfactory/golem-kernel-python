import asyncio
import websockets
import sys

url = sys.argv[1]

async def t1():
    headers = {"Authorization": "Bearer 6f945361959c4888b614e5b6b448d49d"}
    ws = await websockets.connect(url, extra_headers=headers)
    try:
        for i in range(10):
            code = "a=7\nprint(a)\na + 4"
            await ws.send(code.encode())
            print("Message sent, waiting ...")
            print(await ws.recv())
    finally:
        await ws.close()

asyncio.run(t1())
