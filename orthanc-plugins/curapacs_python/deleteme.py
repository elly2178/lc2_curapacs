import asyncio
import websockets

async def consumer_handler(reader, writer):
    print("NEW CONNECTION")
    async for message in reader:
        print("MESSAGE RECEIVED: " + message.decode())

    
loop = asyncio.get_event_loop()
unix_server = asyncio.start_unix_server(consumer_handler, path="/tmp/fuckme.sock")
loop.create_task(unix_server)
loop.run_forever()


"""
start_server = websockets.serve(handler, "0.0.0.0", 8081)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
"""