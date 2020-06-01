import asyncio
import websockets
import json
import logging
import multiprocessing
from curapacs_python import config

class OrthancMessaging:
    """
    Send, Receives and parses messages"
    """
    connected_instances = set()
    queue = asyncio.Queue()


async def producer_handler(websocket, path):
    while True:
        message = await OrthancMessaging.queue.get()
        print(f"Sending Message to all connected instances: {message}")
        if OrthancMessaging.connected_instances:
            await asyncio.wait([orthanc_websocket.send(message) for
                                orthanc_websocket in OrthancMessaging.connected_instances])
        OrthancMessaging.queue.task_done()
        print(f"Sent Message, queue contents are {OrthancMessaging.queue}")

async def consumer_handler(websocket, path):
    async for message in websocket:
        print("MESSAGE RECEIVED: " + message)
    print("consumer_handler returns")

async def OrthancUnixSocketHandler(reader, writer):
    data = await reader.read()
    try:
        data = data.decode()
    except UnicodeDecodeError:
        config.LOGGER.error(f"Failed to decode bytestring from unix socket")
        return
    config.LOGGER.debug(f"OrthancUnixSocketHandler forwarding message to all connected orthancs: {data.decode}")
    await OrthancMessaging.queue.put(data.decode())

async def OrthancMessageHandlerClient(uri):
    while True:
        async with websockets.connect(config.PEER_URI) as websocket_client:
            config.LOGGER.debug(f"Websocket connection established with {config.PEER_URI}")
            pass

async def OrthancMessageHandler(websocket, path):
    OrthancMessaging.connected_instances.add(websocket)
    consumer_task = asyncio.ensure_future(
        consumer_handler(websocket, path))
    producer_task = asyncio.ensure_future(
        producer_handler(websocket, path))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        timeout=config.HTTP_TIMEOUT,
        return_when=asyncio.ALL_COMPLETED,
    )
    #for task in pending:
    #    task.cancel()


event_loop = asyncio.get_event_loop()
if config.PARENT_NAME:
    websocket_server = websockets.serve(OrthancMessageHandler, "0.0.0.0", config.LOCAL_WS_PORT) #config.LOCAL_WS_PORT)
    event_loop.run_until_complete(websocket_server)
else:
    event_loop.run_until_complete(OrthancMessageHandlerClient(config.PEER_URI))
unix_server = asyncio.start_unix_server(OrthancUnixSocketHandler, path=config.LOCAL_UNIX_SOCKET_PATH)
event_loop.run_until_complete(unix_server)
ORTHANC_WEBSOCKET_PROCESS = multiprocessing.Process(target=event_loop.run_forever)
ORTHANC_WEBSOCKET_PROCESS.daemon = True
ORTHANC_WEBSOCKET_PROCESS.start()
