import asyncio
import websockets
import logging
logger = logging.getLogger('websockets')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
#from curapacs_python import config

"""
Run server
Register client when he connects
Extend orthanc-plugins with mwl_server
when mwl_server gets POSTed, run
Timeout https://docs.python.org/3/library/asyncio-task.html#awaitables
"""


async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"

    await websocket.send(greeting)
    print(f"> {greeting}")

start_server = websockets.serve(hello, "localhost", 8765)

event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(start_server)
event_loop.run_forever()
