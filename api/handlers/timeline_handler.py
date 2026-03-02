from uuid import UUID
from sqlmodel import Session
from datetime import datetime
from api.db.managers.timeline_manager import PetitionTimelineManager
from api.db.schema.timeline import PetitionTimeline
from api.consts import PetitionStatus
from sqlalchemy.orm.attributes import flag_modified

class TimelineHandler:
    def __init__(self, db: Session):
        self.manager = PetitionTimelineManager(db)

    def initialize_timeline(self, petition_id: UUID) -> PetitionTimeline:
        """
        Creates the initial timeline for a new petition.
        Initial log: '-' -> 'approver_action'
        """
        berlin_now = datetime.now()
        initial_data = {
            "logs": [
                {
                    "timestamp": berlin_now.isoformat(),
                    "from_status": "-",
                    "to_status": PetitionStatus.APPROVER_ACTION
                }
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

    def log_status_change(self, petition_id: UUID, from_status: str, to_status: str, commit: bool = True) -> PetitionTimeline:
        """
        Logs a status change event to the timeline.
        """
        timeline = self.manager.get_timeline(petition_id)
        if not timeline:
            timeline = self.initialize_timeline(petition_id)
            
        berlin_now = datetime.now()
        new_entry = {
            "timestamp": berlin_now.isoformat(),
            "from_status": from_status,
            "to_status": to_status
        }
        
        data = dict(timeline.data)
        if "logs" not in data:
            data["logs"] = []
            
        data["logs"].append(new_entry)
        timeline.data = data
        flag_modified(timeline, "data")
        timeline.last_updated_at = berlin_now
        
        return self.manager.update_timeline(timeline, commit=commit)
