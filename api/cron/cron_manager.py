import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from api.db.dependencies import engine
from api.db.schema.petition import Petition
from api.db.schema.timeline import PetitionTimeline
from api.handlers.petition_handler import PetitionHandler
from api.consts import (
    PetitionStatus, 
    STUDENT_NOTIFCATION, STUDENT_NOTIFICATION_INTERVAL,
    APPROVER_NOTIFICATION, APPROVER_NOTIFICATION_INTERVAL,
    SUPERVISOR_NOTIFICATION, SUPERVISOR_NOTIFICATION_INTERVAL
)
from datetime import datetime

logger = logging.getLogger(__name__)

class CronManager:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        # Schedule the watcher to run every day at midnight (00:00)
        self.scheduler.add_job(
            self.watcher,
            CronTrigger(hour=0, minute=0),
            id='petition_watcher',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("CronManager initialized and background scheduler started.")

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("CronManager scheduler shut down.")

    def watcher(self):
        """
        Runs daily. Retrieves all petitions and their timelines, evaluates inactivity delays,
        and triggers warning or deletion pipelines accordingly.
        """
        logger.info("Starting daily petition watcher job...")
        try:
            with Session(engine) as session:
                handler = PetitionHandler(session)
                results = handler.get_petitions_with_timeline()
                
                logger.info(f"Watcher found {len(results)} petitions to evaluate.")
                
                for petition, timeline in results:
                    if not timeline:
                        continue
                        
                    status = petition.status
                    role = None
                    max_notif = 0
                    interval_days = 0
                    
                    if status in [PetitionStatus.APPROVER_REVISION, PetitionStatus.STUDENT_REVISION]:
                        role = "supervisor"
                        max_notif = SUPERVISOR_NOTIFICATION
                        interval_days = SUPERVISOR_NOTIFICATION_INTERVAL
                    elif status == PetitionStatus.APPROVER_ACTION:
                        role = "approver"
                        max_notif = APPROVER_NOTIFICATION
                        interval_days = APPROVER_NOTIFICATION_INTERVAL
                    elif status in [PetitionStatus.STUDENT_ACTION, PetitionStatus.CLERK_REVISION]:
                        role = "student"
                        max_notif = STUDENT_NOTIFCATION
                        interval_days = STUDENT_NOTIFICATION_INTERVAL
                    else:
                        continue 
                    
                    notifications_data = timeline.data.get("notifications", {})
                    role_data = notifications_data.get(role, {"count": 0, "last_sent": None})
                    
                    count = role_data.get("count", 0)
                    last_sent_str = role_data.get("last_sent")
                    
                    if last_sent_str:
                        last_sent = datetime.fromisoformat(last_sent_str)
                        days_passed = (datetime.now() - last_sent).days
                    else:
                        last_sent = timeline.last_updated_at
                        days_passed = (datetime.now() - last_sent).days
                        
                    if days_passed >= interval_days:
                        if count >= max_notif:
                            logger.info(f"Petition {petition.id} expired for {role}. Deleting.")
                            handler.handle_inactivity_deletion(petition.id, role)
                        else:
                            logger.info(f"Petition {petition.id} inactive for {role}. Sending warning ({count + 1}/{max_notif}).")
                            handler.handle_inactivity_warning(petition.id, role)
                    
        except Exception as e:
            logger.error(f"Error during watcher execution: {e}")
