"""
Subjects and bodies of all mails sent by the EmailHandler.

Bodies are str.format templates, rendered by EmailHandler._render_body, which
appends the footer and joins the German and English part with the separator.
Placeholders available in every body: {petition_id}, {support_mail}, {frontend_url}.
Any other placeholder must be passed by the sending method.
"""

SEPARATOR = "\n\n--------------\n\n"

FOOTER_DE = (
    "\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software Clockwork. "
    "Bei Fragen oder Problemen wenden Sie sich bitte an {support_mail}.\n"
)

FOOTER_EN = (
    "\nYou are receiving this email as part of student employment process of the software, Clockwork. "
    "If you have any questions or encounter any problems, please email {support_mail}.\n"
)

# --- Petition created ---------------------------------------------------------

PETITION_CREATED_STUDENT_SUBJECT = "[ClockWork] Neuer Antrag erstellt / New application created"
PETITION_CREATED_STUDENT_BODY_DE = (
    "Ihr Antrag {petition_id} für die Einstellung als studentische Hilfskraft wurde von Ihrem Vorgesetzten "
    "erstellt und wird nun von den Kostenstellenverantwortlichen geprüft.\n"
)
PETITION_CREATED_STUDENT_BODY_EN = (
    "Your application {petition_id} for employment as a student assistant has been created by your supervisor "
    "and is now pending review by the budget approvers.\n"
)

# Placeholders: {budget_position}, {approval_url}
APPROVAL_REQUEST_APPROVER_SUBJECT = (
    "[ClockWork] Neuer Antrag (Einstellung stud. Hilfskraft) / New approval request (new student assistant)"
)
APPROVAL_REQUEST_APPROVER_BODY_DE = (
    "Sie haben einen Antrag  für die Einstellung einer studentischen Hilfskraft auf die Kostenstelle "
    "{budget_position} erhalten und müssen diesen freigeben.\n\n"
    "Mit diesem Link gelangen Sie zum Antrag und können diesen genehmigen, ablehnen oder eine Änderung "
    "anfordern: {approval_url}\n"
)
APPROVAL_REQUEST_APPROVER_BODY_EN = (
    "You received an approval request for the employment of a new student assistant on the budget position "
    "{budget_position}.\n\n"
    "Please use the link to review the request. You can either approve or reject the request or you can "
    "demand a revision: {approval_url}\n"
)

# --- Budget approved (all budget positions) -----------------------------------

BUDGET_APPROVED_SUBJECT = "[ClockWork] Kostenstellen freigegeben / Budget approved"
BUDGET_APPROVED_SUPERVISOR_BODY_DE = (
    "Ihr Antrag {petition_id} für die Einstellung einer studentischen Hilfskraft wurde von allen "
    "Kostenstellenverantwortlichen freigegeben.\n"
)
BUDGET_APPROVED_SUPERVISOR_BODY_EN = (
    "Your application {petition_id} for the employment of a new student assistant has been approved by all "
    "budget approvers.\n"
)
BUDGET_APPROVED_APPROVER_BODY_DE = (
    "Der Antrag {petition_id} für die Einstellung einer studentischen Hilfskraft wurde von allen "
    "Kostenstellenverantwortlichen freigegeben.\n"
)
BUDGET_APPROVED_APPROVER_BODY_EN = (
    "The application {petition_id} for the employment of a new student assistant has been approved by all "
    "budget approvers.\n"
)

# Fast track for students with an approved petition in the same semester. Placeholders: {acceptance_url}
ACCEPTANCE_LINK_STUDENT_SUBJECT = "[ClockWork] Antrag freigegeben / Application approved"
ACCEPTANCE_LINK_STUDENT_BODY_DE = (
    "Ihr Antrag {petition_id} für die Einstellung als studentische Hilfskraft wurde von allen "
    "Kostenstellenverantwortlichen freigegeben.\n\n"
    "Bitte bestätigen Sie den Antrag unter folgendem Link:\n{acceptance_url}\n"
)
ACCEPTANCE_LINK_STUDENT_BODY_EN = (
    "Your application {petition_id} for employment as a student assistant has been approved by all "
    "budget approvers.\n\n"
    "Please confirm your application at the following link:\n{acceptance_url}\n"
)

# Placeholders: {dashboard_url}
UPLOAD_REQUEST_STUDENT_SUBJECT = "[ClockWork] Dokumente hochladen / Upload Documents Required"
UPLOAD_REQUEST_STUDENT_BODY_DE = (
    "Für Sie wurde ein Antrag zur Einstellung als studentische Hilfskraft gestellt. Laden Sie dazu die "
    "notwendigen Unterlagen hoch. Benötigt werden\n\n"
    "- Selbstauskunft zur Lohnsteuererklärung (ELStAM)\n\n"
    "- Fragebogen zur Sozialversicherung\n\n"
    "- aktuelle Studienbescheinigung\n\n"
    "- Mitgliedsbescheinigung Ihrer Krankenkasse\n\n"
    "Das Student-Dashboard ist unter folgendem Link erreichbar: {dashboard_url}\n"
)
UPLOAD_REQUEST_STUDENT_BODY_EN = (
    "An application has been filed for your employment as a student assistant. Please upload the required "
    "documents to complete your petition. You will need to uploade\n\n"
    "- Self-disclosure form for income tax (ELStAM form)\n\n"
    "- Social Security questionnaire\n\n"
    "- current certificate of enrolment\n\n"
    "- Health insurance membership certificate\n\n"
    "The student dashboard can be accessed from this link: {dashboard_url}\n"
)

# --- Revision requested (shared default subject) ------------------------------

REVISION_REQUESTED_SUBJECT = "[ClockWork] Änderungen angefordert / Changes requested"

# --- Revision requested by a budget approver ----------------------------------

NO_REVISION_MESSAGE = "No specific message provided."

# Placeholders: {requesting_approver}, {message}
APPROVER_REVISION_SUPERVISOR_BODY_DE = (
    "Der Kostenstellenverantwortliche {requesting_approver} hat eine Änderung an Ihrem Antrag {petition_id} "
    "angefordert:\n\n"
    "{message}\n\n"
    "Bitte melden Sie sich an, um die Änderungen vorzunehmen.\n"
)
APPROVER_REVISION_SUPERVISOR_BODY_EN = (
    "The budget approver {requesting_approver} has requested changes to your application {petition_id}:\n\n"
    "{message}\n\n"
    "Please log in to make the requested changes.\n"
)
APPROVER_REVISION_APPROVER_BODY_DE = (
    "Der Kostenstellenverantwortliche {requesting_approver} hat eine Änderung an dem Antrag {petition_id} "
    "angefordert:\n\n"
    "{message}\n\n"
    "Sie werden benachrichtigt, sobald die Änderungen vorgenommen wurden.\n"
)
APPROVER_REVISION_APPROVER_BODY_EN = (
    "The budget approver {requesting_approver} has requested changes to application {petition_id}:\n\n"
    "{message}\n\n"
    "You will be notified once the changes have been made.\n"
)
