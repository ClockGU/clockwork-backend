from sqlalchemy import event
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.orm import object_session
import asyncio
import logging

from api.db.schema.petition import Petition
from api.consts import PetitionStatus
from api.websockets.routers.web_socket import send_serialized_data_to_clerks
from api.handlers.petition_handler import PetitionHandler
from api.pydantic_models import PetitionRead

logger = logging.getLogger(__name__)

def petition_after_update(mapper, connection, target):
    """
    Event listener for Petition updates.
    Checks if the status has changed to a clerk-relevant status.
    If so, sends all clerk-relevant petitions via WebSocket.
    """
    hist = get_history(target, 'status')
    
    if hist.has_changes():
        new_status = target.status
        relevant_statuses = [
            PetitionStatus.AWAITING_SIGNATURE, 
            PetitionStatus.COMPLETED, 
            PetitionStatus.CLERK_REVISION, 
            PetitionStatus.CLERK_ACTION
        ]

        if new_status in relevant_statuses:
            logger.info(f"Petition {target.id} status changed to {new_status}. Notifying clerks.")
            try:
                session = object_session(target)
                if session:
                    handler = PetitionHandler(session)
                    petitions = handler.get_petitions_clerk()

                    logger.info(f"Found {len(petitions)} clerk petitions to send.")

                    petition_data = [
                        PetitionRead.model_validate(p, from_attributes=True).model_dump(mode="json")
                        for p in petitions
                    ]

                    loop = asyncio.get_running_loop()
                    loop.create_task(send_serialized_data_to_clerks(petition_data))
                else:
                    logger.warning("No session found for petition object. Skipping WebSocket notification.")

            except RuntimeError:
                logger.warning("No running asyncio loop. Skipping WebSocket notification.")
            except Exception as e:
                logger.error(f"Failed to schedule WebSocket notification: {e}")

def register_petition_events():
    event.listen(Petition, 'after_update', petition_after_update)
