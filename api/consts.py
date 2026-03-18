from enum import Enum


class PetitionStatus(str, Enum):
    """Enum for all possible petition statuses"""
    APPROVED = "approved"
    STUDENT_ACTION = "student_action"
    APPROVER_ACTION = "approver_action"
    APPROVER_REVISION = "approver_revision"
    STUDENT_REVISION = "student_revision"
    CLERK_ACTION = "clerk_action"
    CLERK_REVISION = "clerk_revision"
    AWAITING_SIGNATURE = "awaiting_signature"
    COMPLETED = "completed"


# PDF Form Field Names
NAME_FIELD="SHK_Name"
BIRTHDAY_FIELD="SHK_Geburtsdatum"
ADDRESS_FIELD="SHK_Wohnort"
CONTRACT_START_FIELD="SHK_Vertragsbeginn"
CONTRACT_END_FIELD="SHK_Vertragsende"
DEBIT_WORKTIME_FIELD="SHK_Sollarbeitszeit"
SIGNITURE_DATE_FIELD="Freigabe_Datum"
CONTRACT_PDF_TEMPLATE="SHK_Arbeitsvertrag_ab_01-02-2025_Rv5_Plain.pdf"
PDF_TEMPLATE_DIR="api/pdf/templates/"
PERSONAL_DATA_PDF_TEMPLATE="SHK_Personal-Stammdatenblatt_ab_01_01_2025_Plain.pdf"


### Cron Job configuration##
CRONJOB_INTERVAL_HOURS = 24
STUDENT_NOTIFCATION = 2 # It controls how many times student shall be informed before deleting the petition.
STUDENT_NOTIFICATION_INTERVAL = 3 # After How many days Student shall be informed. 3 means after every 3 days student will be informed.
APPROVER_NOTIFICATION = 2 # It controls how many times approver shall be informed before deleting the petition.
APPROVER_NOTIFICATION_INTERVAL = 3 # After How many days Approver shall be informed. 3 means after every 3 days approver will be informed.
SUPERVISOR_NOTIFICATION = 2 # It controls how many times supervisor shall be informed before deleting the petition.
SUPERVISOR_NOTIFICATION_INTERVAL = 3 # After How many days Supervisor shall be informed. 3 means after every 3 days supervisor will be informed.

