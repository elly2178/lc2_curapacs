
import asyncio
import websockets

async def hello():
    uri = "ws://c0100-orthanc.curapacs.ch/ws"

    async with websockets.connect(uri, extra_headers=[("Authorization", "Basic b3J0aGFuYzpvcnRoYW5j")]) as websocket:
        while True:
            name = input("What's your name? ")
            await websocket.send(name)
            greeting = await websocket.recv()
            print(f"< {greeting}")
        


asyncio.get_event_loop().run_until_complete(hello())