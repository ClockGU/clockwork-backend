from typing import Dict
from fastapi import WebSocket, APIRouter, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)


manager = ConnectionManager()

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):

    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(client_id, f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)

async def send_data_to_socket(user_id: str, data: str):
    """
    Send data to a specific WebSocket connection using the user ID.

    Args:
        user_id (str): The ID of the user (client_id) to send the data to.
        data (str): The data to send through the WebSocket.
    """
    print("about to send data", flush=True)
    await manager.send_message(user_id, data)

import json
@router.post("/send-data/{user_id}")
async def send_data(user_id: str):
    """
    API endpoint to send data to a specific WebSocket connection.

    Args:
        user_id (str): The ID of the user (client_id) to send the data to.

    Returns:
        dict: A response indicating success or failure.
    """
    try:
        # Send sample data to the WebSocket
        await send_data_to_socket(user_id, json.dumps({23: 'Hello World'}))

        return {"success": True, "message": "Data sent successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}