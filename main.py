import json
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_personal_json(self, data: json, websocket: WebSocket):
        await websocket.send_json(data)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast_json(self, data: json):
        for connection in self.active_connections:
            await connection.send_json(data)


app = FastAPI()
app.mount("/vue-app", StaticFiles(directory='vue-app'), name='static')

manager = ConnectionManager()

html = ''
with open('index.html', 'r') as file:
    html = file.read()


@app.get('/')
async def get():
    return RedirectResponse('vue-app/index.html')


@app.get('/static/html')
async def get():
    return HTMLResponse(html)


@app.websocket('/ws/echo')
async def websocket_echo(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.send_personal_message(f'Hello there!', websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.send_personal_message(f'You wrote "{message}"', websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket('/ws/api/v1')
async def websocket_api(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.send_personal_json({
        'hello': 'there!',
    }, websocket)
    # await manager.send_personal_message(json.dumps({
    #    'connected': True,
    # }), websocket)
    try:
        while True:
            message = await websocket.receive_json()
            print(message)
            await manager.send_personal_json({
                'request': message,
                'response': 'ok'
            }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    await manager.broadcast(f'Client #{client_id} connected to the chat')
    try:
        while True:
            message = await websocket.receive_text()
            await manager.send_personal_message(f'You wrote: "{message}"', websocket)
            await manager.broadcast(f'Client #{client_id} wrote: "{message}"')
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f'Client #{client_id} left the chat')


async def periodic_message():
    """ Periodic task """
    counter = 0;
    while True:
        counter += 1
        await manager.broadcast_json({
            'counter': counter,
            'text': 'Hello, world!'
        })
        await asyncio.sleep(5)


loop = asyncio.get_event_loop()
task = loop.create_task(periodic_message())
