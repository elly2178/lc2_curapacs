import asyncio
import websockets
import json
import multiprocessing
import logging
import sys
from curapacs_python import config
from curapacs_python import helpers
from curapacs_python.OrthancHost import OrthancHost
from curapacs_python.OrthancMWLCreator import Worklist


class OrthancMessage:
    """
    Send, Receives and parses messages"
    """
    connected_instances = set()
    queue = asyncio.Queue()

    def __init__(self, message):
        if isinstance(message, str):
            message = json.loads(message)
        self._content = message.get("content", {})
        self._type = message.get("type", "")
    
    @property
    def content(self):
        return self._content
    
    @property
    def type(self):
        return self._type

    def _get_new_worklist(self):
        worklist_id = self.content["id"]
        config.LOGGER.debug(f"Fetching worklist with id: {worklist_id}")
        remote_orthanc = OrthancHost(config.PEER_URI,
                             http_user=config.PEER_HTTP_USER,
                             http_password=config.PEER_HTTP_PASSWORD)
        worklist_as_json, _ = helpers.get_data(f"{remote_orthanc.url}/worklists/{worklist_id}")
        worklist = Worklist(json=json.dumps(worklist_as_json))
        worklist.create_worklist_from_dicom_json(worklist.json)
        config.LOGGER.debug(f"Created new worklist.")

    def parse_by_type(self):
        if self.type == "new_worklist":
            self._get_new_worklist()
        else:
            pass

async def producer_handler(websocket, path):
    while True:
        message = await OrthancMessage.queue.get()
        config.LOGGER.debug(f"Sending message to all connected instances: {message}")
        if OrthancMessage.connected_instances:
            await asyncio.wait([orthanc_websocket.send(message) for
                                orthanc_websocket in OrthancMessage.connected_instances])
        OrthancMessage.queue.task_done()
        print(f"Sent Message, queue contents are {OrthancMessage.queue}")

async def consumer_handler(websocket, path):
    async for message in websocket:
        print("MESSAGE RECEIVED: " + message)
    print("consumer_handler returns")

async def OrthancUnixSocketHandler(reader, writer):
    config.LOGGER.debug(f"OrthancUnixSocketHandler started.")
    #async for message in reader:
    data = await reader.read()
    try:
        data = data.decode()
    except UnicodeDecodeError:
        config.LOGGER.error(f"Failed to decode bytestring from unix socket")
        return
    config.LOGGER.debug(f"OrthancUnixSocketHandler forwarding message to all connected orthancs: {data}")
    await OrthancMessage.queue.put(data)

async def OrthancMessageHandlerClient(uri):
    config.LOGGER.debug("Starting OrthancMessageHandlerClient")
    auth_header = list(helpers.get_http_auth_header(config.PEER_HTTP_USER, config.PEER_HTTP_PASSWORD).items())[0]
    while True:
        try:
            config.LOGGER.debug(f"Websocket client connecting to {uri}")
            async with websockets.connect(uri, extra_headers=[auth_header], 
                                        ping_interval=config.LOCAL_WS_KEEPALIVE_INTERVAL) as websocket_client:
                async for message in websocket_client:
                    config.LOGGER.debug(f"Websocket client received message: {message}")
                    parser = OrthancMessage(message)
                    parser.parse_by_type()
        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidStatusCode):
            config.LOGGER.info(f"Websocket connection terminated, retrying...")
            await asyncio.sleep(5)
    config.LOGGER.debug("Terminating OrthancMessageHandlerClient")

async def OrthancMessageHandler(websocket, path):
    OrthancMessage.connected_instances.add(websocket)
    config.LOGGER.debug(f"Orthanc websocket client registered with server.")
    try:
        consumer_task = asyncio.ensure_future(
            consumer_handler(websocket, path))
        producer_task = asyncio.ensure_future(
            producer_handler(websocket, path))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            timeout=None,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        config.LOGGER.info(f"Orthanc websocket client unregisterd with server.")
        OrthancMessage.connected_instances.remove(websocket)


event_loop = asyncio.get_event_loop()

if not config.PARENT_NAME:
    config.LOGGER.info("Starting websocket server.")
    websocket_server = websockets.serve(OrthancMessageHandler, "0.0.0.0", config.LOCAL_WS_PORT)
    event_loop.run_until_complete(websocket_server)
else:
    config.LOGGER.info("Starting websocket client.")
    event_loop.create_task(OrthancMessageHandlerClient(config.PEER_WS_URI))
unix_server = asyncio.start_unix_server(OrthancUnixSocketHandler, path=config.LOCAL_UNIX_SOCKET_PATH)
event_loop.create_task(unix_server)
ORTHANC_WEBSOCKET_PROCESS = multiprocessing.Process(target=event_loop.run_forever, name="orthanc async manager")
ORTHANC_WEBSOCKET_PROCESS.daemon = True
ORTHANC_WEBSOCKET_PROCESS.start()
