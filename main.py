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
        <h2>Your ID: &nbsp;<input type="text" id="ws-id" autocomplete="off" onchange="connect()"/></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            let ws = undefined;
            let client_id = document.getElementById("ws-id");
            client_id.value = Date.now()+"";
            connect();

            function connect() {
                if (ws !== undefined) {
                    ws.close();
                }
                ws = new WebSocket(`ws://${location.host}/ws/${client_id.value}`);
                ws.onmessage = function(event) {
                    const ulMessages = document.getElementById('messages');
                    const liMessage = document.createElement('li');
                    const content = document.createTextNode(event.data);
                    liMessage.appendChild(content);
                    ulMessages.appendChild(liMessage);
                };
            }
            function sendMessage(event) {
                const input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


class Payload(BaseModel):
    client_id: str
    message: str


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
