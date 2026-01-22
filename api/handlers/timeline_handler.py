from uuid import UUID
from sqlmodel import Session
from datetime import datetime
from zoneinfo import ZoneInfo
from api.db.managers.timeline_manager import PetitionTimelineManager
from api.db.schema.timeline import PetitionTimeline
from api.consts import PetitionStatus

class TimelineHandler:
    def __init__(self, db: Session):
        self.manager = PetitionTimelineManager(db)

    def initialize_timeline(self, petition_id: UUID) -> PetitionTimeline:
        """
        Creates the initial timeline for a new petition.
        Initial log: '-' -> 'approver_action'
        """
        # Create initial data structure
        berlin_now = datetime.now(ZoneInfo("Europe/Berlin"))
        initial_data = {
            "logs": [
                {
                    "timestamp": berlin_now.isoformat(),
                    "from_status": "-",
                    "to_status": PetitionStatus.APPROVER_ACTION                }
            ],
            "notifications": {
                "student": {"count": 0, "last_sent": None},
                "supervisor": {"count": 0, "last_sent": None},
                "approver": {"count": 0, "last_sent": None}
            }
        }

        timeline = PetitionTimeline(
            petition_id=petition_id,
            data=initial_data,
            last_updated_at=berlin_now
        )
        return self.manager.create_timeline(timeline)

    def delete_timeline(self, petition_id: UUID) -> bool:
        """
        Deletes the timeline associated with a petition.
        """
        return self.manager.delete_timeline(petition_id)
