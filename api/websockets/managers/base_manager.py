from collections.abc import Callable

from fastapi import WebSocket
from typing import Dict, Any


class WebsocketConnectionManager:
    def __init__(self, authenticator_func: Callable[[str], Any]):
        self.active_connections: Dict[str, WebSocket] = {}
        self.is_authenticated = False
        self.authenticator = authenticator_func

    def authenticate(self, token: str):
        try:
            self.authenticator(token)
        except Exception as e:
            raise e
        else:
            self.is_authenticated = True

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str, code: int):
        if client_id in self.active_connections:
            await self.active_connections[client_id].close(code)
            self.remove_connection(client_id)

    def remove_connection(self, client_id: str):
        del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: str):
        if client_id in self.active_connections and self.is_authenticated:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)
