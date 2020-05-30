import asyncio
import websockets
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
    while True:
        message = await OrthancMessaging.queue.get()
        await websocket.send(message)

async def consumer_handler(websocket, path):
    async for message in websocket:
        print("MESSAGE RECEIVED: " + message)


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
    print("DONE: " + str(done) + " PENDING: " + str(pending))
    for task in pending:
        task.cancel()


start_server = websockets.serve(OrthancMessageHandler, "0.0.0.0", 8081) #config.LOCAL_WS_PORT)
event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(start_server)
ORTHANC_WEBSOCKET_PROCESS = multiprocessing.Process(target=event_loop.run_forever)
ORTHANC_WEBSOCKET_PROCESS.run()
