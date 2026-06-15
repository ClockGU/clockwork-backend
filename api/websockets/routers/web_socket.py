import asyncio
from typing import Dict, List
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect
)
import logging
from sqlmodel import Session
from json import dumps, JSONEncoder
from uuid import UUID
from datetime import date
import requests

from api.db.dependencies import get_db
from api.handlers import (
    PetitionHandler,
)
from api.env import settings
from api.websockets.managers import ClerkConnectionManager, WebsocketConnectionManager, get_clerk_connection_manager

router = APIRouter()

logger = logging.getLogger(__name__)

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
    clerk_list_api = settings.CLERK_LIST
    response = requests.get(clerk_list_api)
    if response.status_code == 200:
        return response.json().get("clerks", [])
    return []


async def send_serialized_data_to_clerks(data: List[Dict], manager: WebsocketConnectionManager = Depends(get_clerk_connection_manager)):
    """
    Send data to a specific WebSocket connection using the user ID.
    """
    clerks = get_all_clerks()
    for client_id in clerks:
        await manager.send_message(
            client_id,
            dumps({
                "type": "updated_petitions",
                "data": data
            }, cls=UUIDEncoder)
        )


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(client_id: str, websocket: WebSocket,
                             manager: WebsocketConnectionManager = Depends(get_clerk_connection_manager),
                             handler: PetitionHandler = Depends(get_petition_handler)) -> None:

    """
    Websocket for clerks to receive real-time updates on petitions. The clerk must authenticate using a token sent in
    the first message after connecting. If authentication is successful, the clerk will receive the current list of
    pending petitions and any subsequent updates. If authentication fails or if there is a timeout while waiting
    for the authentication message, the connection will be closed with an appropriate status code.
    """

    clerk_ids = get_all_clerks()
    if client_id not in clerk_ids:
        raise RuntimeError(f"Invalid user id: {client_id}")

    await manager.connect(client_id, websocket)
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
    except asyncio.TimeoutError:
        logger.warning(f"Authentication timeout for client_id: {client_id}")
        await manager.disconnect(client_id, 1008)
        return

    if data.get("type", "") == "auth" and data.get("token", None) is not None:
        manager.authenticate(data.get("token"))

    if manager.is_authenticated:
        petitions = handler.get_petitions_clerk()
        await manager.send_message(
            client_id,
            dumps({
                "type": "new_petition",
                "data": [petition.dict(by_alias=True, exclude_none=True) for petition in petitions]
            }, cls=UUIDEncoder)
        )
    else:
        await manager.disconnect(client_id, 1008)
        return
    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        manager.remove_connection(client_id)
