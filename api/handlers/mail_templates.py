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
