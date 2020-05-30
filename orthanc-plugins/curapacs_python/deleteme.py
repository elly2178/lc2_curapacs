import asyncio
import websockets


queue = asyncio.Queue()
queue.put_nowait("FUBAR")

async def producer_handler(websocket, path):
    while True:
        message = await queue.get()
        await websocket.send(message)

async def consumer_handler(websocket, path):
    print("NEW CONNECTION")
    async for message in websocket:
        print("MESSAGE RECEIVED: " + message)


async def handler(websocket, path):
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
    
"""
start_server = websockets.serve(handler, "0.0.0.0", 8081)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
"""