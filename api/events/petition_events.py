from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history
import asyncio
import logging

from api.db.schema.petition import Petition
from api.consts import PetitionStatus
from api.routers.web_socket import send_data_to_clerks
from api.handlers.petition_handler import PetitionHandler
from api.handlers.timeline_handler import TimelineHandler

logger = logging.getLogger(__name__)

def session_before_flush(session, flush_context, instances):
    """
    Event listener called before session flush.
    Iterates over modified instances to:
    1. Log status changes to PetitionTimeline.
    2. Notify clerks of status changes via WebSocket.
    """
    for target in session.dirty:
        if not isinstance(target, Petition):
            continue

        hist = get_history(target, 'status')
        if hist.has_changes():
            new_status = target.status
            old_status = hist.deleted[0] if hist.deleted else None
            
            try:
                timeline_handler = TimelineHandler(session)
                timeline_handler.log_status_change(target.id, old_status, new_status, commit=False)
            except Exception as e:
                logger.error(f"Failed to log timeline event: {e}")

            relevant_statuses = [
                PetitionStatus.AWAITING_SIGNATURE, 
                PetitionStatus.COMPLETED, 
                PetitionStatus.CLERK_REVISION, 
                PetitionStatus.CLERK_ACTION
            ]

            if new_status in relevant_statuses:
                logger.info(f"Petition {target.id} status changed to {new_status}. Notifying clerks.")
                try:
                    handler = PetitionHandler(session)
                    petitions = handler.get_petitions_clerk()
                    logger.info(f"Found {len(petitions)} clerk petitions to send.")
                    
                    petitions_data = [p.dict(by_alias=True, exclude_none=True) for p in petitions]

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(send_data_to_clerks(petitions_data))
                    except RuntimeError:
                        logger.warning("No running asyncio loop. Skipping WebSocket notification.")
                        
                except Exception as e:
                    logger.error(f"Failed to schedule WebSocket notification: {e}")

def register_petition_events():
    event.listen(Session, 'before_flush', session_before_flush)
