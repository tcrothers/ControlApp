from app import app
import trio
import json
from functools import wraps


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print("wrapping: adding connection")
        app.xps_watchers.add(websocket._get_current_object())
        try:
            return await func(*args, **kwargs)
        finally:
            print("wrapper: removing connection")
            app.xps_watchers.remove(websocket._get_current_object())
    return wrapper


async def broadcast(message: str):
    active = len(app.xps_watchers)
    for websock in app.xps_watchers:
        await websock.send(message)


@app.websocket('/ws')
@collect_websocket
async def ws():
    while True:
        msg = await websocket.receive()
        stage, new_stage_pos = msg.split(":")
        # async with trio.open_nursery() as nursery:
        moving = trio.Event()
        app.nursery.start_soon(stages[stage].move_to, new_stage_pos, moving)
        app.nursery.start_soon(stages[stage].broadcast_position, moving)
        # await websocket.send(f"{stages[stage].to_json()}")
