import asyncio
import websockets
import json
import logging
import multiprocessing
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
#from config import config

class OrthancMessaging:
    """
    Send, Receives and parses messages"
    """
    connected_instances = set()
    queue = asyncio.Queue()

async def producer_handler(websocket, path):
    message = await OrthancMessaging.queue.get()
    print(f"Sending Message to all connected instances: {message}")
    if OrthancMessaging.connected_instances:
        await asyncio.wait([orthanc_websocket.send(message) for
                            orthanc_websocket in OrthancMessaging.connected_instances])
    await OrthancMessaging.queue.task_done()
    print(f"Sent Message, queue contents are {OrthancMessaging.queue}")

async def consumer_handler(websocket, path):
    async for message in websocket:
        print("MESSAGE RECEIVED: " + message)

async def OrthancUnixSocketHandler(reader, writer):
    data = await reader.read()
    print("OrthancUnixSocketHandler got message" + data.decode())
    await OrthancMessaging.queue.put(data.decode())

async def OrthancMessageHandler(websocket, path):
    OrthancMessaging.connected_instances.add(websocket)
    consumer_task = asyncio.ensure_future(
        consumer_handler(websocket, path))
    producer_task = asyncio.ensure_future(
        producer_handler(websocket, path))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    #for task in pending:
    #    task.cancel()


websocket_server = websockets.serve(OrthancMessageHandler, "0.0.0.0", 8081) #config.LOCAL_WS_PORT)
unix_server = asyncio.start_unix_server(OrthancUnixSocketHandler, path="/tmp/curapacs_socket")
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(websocket_server)
event_loop.run_until_complete(unix_server)
ORTHANC_WEBSOCKET_PROCESS = multiprocessing.Process(target=event_loop.run_forever)
ORTHANC_WEBSOCKET_PROCESS.daemon = True
ORTHANC_WEBSOCKET_PROCESS.start()
