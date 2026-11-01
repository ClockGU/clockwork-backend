from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Dict

from fastapi import WebSocket
from starlette.websockets import WebSocketState


@dataclass
class Connection:
    client_id: str
    websocket: WebSocket
    is_authenticated: bool = False


@dataclass
class ConnectionArray:
    connections: Dict[str, Connection] = field(default_factory=dict)

    def add(self, connection: Connection):
        self.connections[connection.client_id] = connection

    async def remove(self, client_id: str, code: int = 1008):
        connection = self.connections.get(client_id)
        if (
            connection
            and connection.websocket.application_state == WebSocketState.CONNECTED
        ):
            await self.connections[client_id].websocket.close(code)
        del self.connections[client_id]

    def authenticate_connection(self, client_id: str):
        if client_id in self.connections:
            self.connections[client_id].is_authenticated = True

    def get_connection(self, client_id: str) -> Connection | None:
        return self.connections.get(client_id)

    def __iter__(self):
        return iter(self.connections.values())


class WebsocketConnectionManager:
    def __init__(self, authenticator_func: Callable[[str], Any]):
        self.active_connections: ConnectionArray = ConnectionArray()
        self.authenticator = authenticator_func

    def authenticate(
        self,
        client_id: str,
        token: str,
    ):
        try:
            self.authenticator(token)
        except Exception as e:
            raise e
        else:
            self.active_connections.authenticate_connection(client_id)

    def is_authenticated(self, client_id: str) -> bool:
        connection = self.active_connections.get_connection(client_id)
        return connection.is_authenticated if connection else False

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(
            Connection(client_id=client_id, websocket=websocket)
        )

    async def disconnect(self, client_id: str, code: int):
        connection = self.active_connections.get_connection(client_id)
        if connection is not None:
            await self.active_connections.remove(client_id, code)

    async def send_message(self, client_id: str, message: str):
        connection = self.active_connections.get_connection(client_id)
        if connection is not None:
            if connection.is_authenticated:
                await connection.websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            if connection.is_authenticated:
                await connection.websocket.send_text(message)
