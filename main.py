import os
from contextlib import asynccontextmanager

import anyio
from broadcaster import Broadcast
from fastapi import (
    FastAPI,
    WebSocket,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse
)
from pydantic import BaseModel


class Payload(BaseModel):
    client_id: str
    message: str


broadcast = Broadcast(os.getenv("REDIS_URL") or "redis://localhost:6379")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Connecting to redis")
    await broadcast.connect()
    print("Connected to redis")
    yield
    print("Disconnecting from redis")
    await broadcast.disconnect()
    print("Disconnected from redis")


app = FastAPI(lifespan=lifespan)

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://${location.host}/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.post("/send")
async def send_message(msg: Payload):
    await broadcast.publish(channel=msg.client_id, message=msg.message)
    return JSONResponse({"status": "ok"})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    print(f"PID: {os.getpid()} connected")
    await websocket.accept()

    async with anyio.create_task_group() as task_group:
        async def run_chatroom_ws_receiver() -> None:
            await chatroom_ws_receiver(websocket=websocket, channel=client_id)
            task_group.cancel_scope.cancel()

        task_group.start_soon(run_chatroom_ws_receiver)
        await chatroom_ws_sender(websocket, client_id)


async def chatroom_ws_receiver(websocket, channel):
    async for message in websocket.iter_text():
        await broadcast.publish(channel=channel, message=message)


async def chatroom_ws_sender(websocket, channel):
    async with broadcast.subscribe(channel=channel) as subscriber:
        async for event in subscriber:
            await websocket.send_text(event.message)
