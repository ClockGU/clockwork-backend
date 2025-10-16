from typing import Dict
from fastapi import  (
    APIRouter, 
    Depends,
    WebSocket, 
    WebSocketDisconnect
)
from sqlmodel import Session
from json import dumps, JSONEncoder
from uuid import UUID
from datetime import date

from api.db.dependencies import get_db
from api.handlers import (
    PetitionHandler,
    ConnectionManager
    )


manager = ConnectionManager()

router = APIRouter()

class UUIDEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)  # Convert UUID to string
        if isinstance(obj, date):
            return obj.isoformat()  # Convert date to ISO 8601 string
        return super().default(obj)
    
def get_petition_handler(
        db: Session = Depends(get_db)
        ) -> PetitionHandler:
    return PetitionHandler(db)

def get_all_clerks():
    # when there are clerks this function will get clerk id's from hr-login-backend
    return ["1234","12345"]

async def send_data_to_clerks(data: str):
    """
    Send data to a specific WebSocket connection using the user ID.

    """
    clerks = get_all_clerks()
    for client_id in clerks:
        await manager.send_message(
            client_id, 
             dumps({
                "type": "updated_petitions",
                "data": [petition.dict(by_alias=True, exclude_none=True) for petition in data] 
            }, cls=UUIDEncoder)
        )

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    client_id: str,
    websocket: WebSocket, 
    handler: PetitionHandler = Depends(get_petition_handler),
    ):

    await manager.connect(client_id, websocket)

    # On connection, send the current petitions to the client
    petitions = handler.get_petitions_clerk()
    await manager.send_message(
        client_id, 
        dumps({
                "type": "new_petition",
                "data": [petition.dict(by_alias=True, exclude_none=True) for petition in petitions] 
            }, cls=UUIDEncoder)
    )
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(client_id, f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)

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
        await send_data_to_clerks(json.dumps({23: 'Hello World'}))

        return {"success": True, "message": "Data sent successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}