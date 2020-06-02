import asyncio
import websockets
import json
import multiprocessing
from curapacs_python import config
from curapacs_python import helpers

class OrthancMessaging:
    """
    Send, Receives and parses messages"
    """
    connected_instances = set()
    queue = asyncio.Queue()


async def producer_handler(websocket, path):
    while True:
        message = await OrthancMessaging.queue.get()
        config.LOGGER.debug(f"Sending Message to all connected instances: {message}")
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
    config.LOGGER.debug(f"OrthancUnixSocketHandler started.")
    async for message in reader:
        #data = await reader.read()
        try:
            data = message.decode()
        except UnicodeDecodeError:
            config.LOGGER.error(f"Failed to decode bytestring from unix socket")
            return
        config.LOGGER.debug(f"OrthancUnixSocketHandler forwarding message to all connected orthancs: {data}")
        await OrthancMessaging.queue.put(data)

async def OrthancMessageHandlerClient(uri):
    config.LOGGER.debug(" OrthancMessageHandlerClient")
    auth_header = list(helpers.get_http_auth_header(config.PEER_HTTP_USER, config.PEER_HTTP_PASSWORD).items())[0]
    while True:
        config.LOGGER.debug(f"Websocket client connecting to {uri}")
        async with websockets.connect(uri, extra_headers=[auth_header]) as websocket_client:
            async for message in websocket_client:
                print("GOT MESSAGE: " + message)
    config.LOGGER.debug("Terminating OrthancMessageHandlerClient")

async def OrthancMessageHandler(websocket, path):
    OrthancMessaging.connected_instances.add(websocket)
    config.LOGGER.debug(f"Orthanc websocket client registered with server.")
    try:
        consumer_task = asyncio.ensure_future(
            consumer_handler(websocket, path))
        producer_task = asyncio.ensure_future(
            producer_handler(websocket, path))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            timeout=config.HTTP_TIMEOUT,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        config.LOGGER.info(f"Orthanc websocket client unregisterd with server.")
        OrthancMessaging.connected_instances.remove(websocket)


event_loop = asyncio.get_event_loop()
if not config.PARENT_NAME:
    config.LOGGER.info("Starting websocket server.")
    websocket_server = websockets.serve(OrthancMessageHandler, "0.0.0.0", config.LOCAL_WS_PORT)
    event_loop.run_until_complete(websocket_server)
else:
    config.LOGGER.info("Starting websocket client.")
    event_loop.create_task(OrthancMessageHandlerClient("ws://c0100-orthanc.curapacs.ch/ws"))
unix_server = asyncio.start_unix_server(OrthancUnixSocketHandler, path=config.LOCAL_UNIX_SOCKET_PATH)
event_loop.create_task(unix_server)
ORTHANC_WEBSOCKET_PROCESS = multiprocessing.Process(target=event_loop.run_forever, name="orthanc async manager")
ORTHANC_WEBSOCKET_PROCESS.daemon = True
ORTHANC_WEBSOCKET_PROCESS.start()
