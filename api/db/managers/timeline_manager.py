from uuid import UUID
from sqlmodel import Session, select
from typing import Optional
from api.db.schema.timeline import PetitionTimeline

class PetitionTimelineManager:
    def __init__(self, db: Session):
        self.db = db

    def create_timeline(self, timeline: PetitionTimeline) -> PetitionTimeline:
        self.db.add(timeline)
        self.db.commit()
        self.db.refresh(timeline)
        return timeline

    def get_timeline(self, petition_id: UUID) -> Optional[PetitionTimeline]:
        statement = select(PetitionTimeline).where(PetitionTimeline.petition_id == petition_id)
        return self.db.execute(statement).scalars().first()

    def update_timeline(self, timeline: PetitionTimeline, commit: bool = True) -> PetitionTimeline:
        self.db.add(timeline)
        if commit:
            self.db.commit()
            self.db.refresh(timeline)
        return timeline

    def delete_timeline(self, petition_id: UUID) -> bool:
        timeline = self.get_timeline(petition_id)
        if not timeline:
            return False
        self.db.delete(timeline)
        self.db.commit()
        return True
