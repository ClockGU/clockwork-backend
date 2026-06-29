from enum import Enum


class PetitionStatus(str, Enum):
    """Enum for all possible petition statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
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
LEGAL_REGULAR_WORKTIME = 2400 # 40 hours * 60 minutes as per legal requirements
LEGAL_REGULAR_CONTRACT_LENGTH = 364 # 1 year in days minus 1 for inclusive dates