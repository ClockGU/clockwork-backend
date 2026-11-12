"""
Subjects and bodies of all mails sent by the EmailHandler.

Bodies are str.format templates, rendered by EmailHandler._render_body, which
appends the footer and joins the German and English part with the separator.
Placeholders available in every body: (Id: {petition_id}), {support_mail}, {frontend_url}.
Any other placeholder must be passed by the sending method.
"""

SEPARATOR = "\n\n--------------\n\n"

FOOTER_DE = (
    "\nSie bekommen diese Mail im Rahmen des SHK-Einstellungsprozesses der Software ClockWork. "
    "Bei Fragen oder Problemen wenden Sie sich bitte an {support_mail}.\n"
)

FOOTER_EN = (
    "\nYou are receiving this email as part of student employment process of the software, ClockWork. "
    "If you have any questions or encounter any problems, please email {support_mail}.\n"
)

# --- Petition created ---------------------------------------------------------

PETITION_CREATED_STUDENT_SUBJECT = "[ClockWork] Neuer Antrag erstellt / New hiring petition created"
PETITION_CREATED_STUDENT_BODY_DE = (
    "Es wurde ein Antrag auf Einstellung (Id: {petition_id}) als studentische Hilfskraft für Sie gestellt."
    "Der Antrag wird nun von den Kostenstellenverantwortlichen geprüft."
    "Nach dieser Prüfung werden Sie über weitere Schritte informiert.\n"
)
PETITION_CREATED_STUDENT_BODY_EN = (
    "A hiring petition (Id: {petition_id}) for employment as student assistant has been submitted for you."
    "The petition is currently reviewed by the budget approvers."
    "You will be informed about further steps after successful approval by the budget approvers \n"
)

# Placeholders: {budget_position}, {approval_url}
APPROVAL_REQUEST_APPROVER_SUBJECT = (
    "[ClockWork] Neue Antragsgenehmigung / New approval request"
)
APPROVAL_REQUEST_APPROVER_BODY_DE = (
    "Sie haben einen neuen Antrag für die Einstellung einer studentischen Hilfskraft auf die Kostenstelle "
    "{budget_position} erhalten und müssen diesen freigeben.\n\n"
    "Mit diesem Link gelangen Sie zum Antrag und können diesen genehmigen, ablehnen oder eine Änderung "
    "anfordern: {approval_url}"
    "Der Link ist ohne Passwortauthentifizierung zugänglich und somit vertraulich zu behandeln.\n"
)
APPROVAL_REQUEST_APPROVER_BODY_EN = (
    "You received an approval request for the employment of a new student assistant on the budget position "
    "{budget_position}.\n\n"
    "The the submitted hiring petition is accessible via this link where you can either approve or reject the petition or "
    "request changes: {approval_url}\n"
)

# --- Budget approved (all budget positions) -----------------------------------

BUDGET_APPROVED_SUBJECT = "[ClockWork] Kostenstelle(n) freigegeben / Budget approver(s) approved"
BUDGET_APPROVED_SUPERVISOR_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) für die Einstellung einer studentischen Hilfskraft wurde von allen "
    "Kostenstellenverantwortlichen freigegeben.\n"
)
BUDGET_APPROVED_SUPERVISOR_BODY_EN = (
    "Your application (Id: {petition_id}) for the employment of a new student assistant has been approved by all "
    "budget approvers.\n"
)
BUDGET_APPROVED_APPROVER_BODY_DE = (
    "Der Antrag (Id: {petition_id}) für die Einstellung einer studentischen Hilfskraft wurde von allen "
    "Kostenstellenverantwortlichen freigegeben.\n"
)
BUDGET_APPROVED_APPROVER_BODY_EN = (
    "The application (Id: {petition_id}) for the employment of a new student assistant has been approved by all "
    "budget approvers.\n"
)

# Fast track for students with an approved petition in the same semester. Placeholders: {acceptance_url}
ACCEPTANCE_LINK_STUDENT_SUBJECT = "[ClockWork] Antrag freigegeben / Application approved"
ACCEPTANCE_LINK_STUDENT_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) für die Einstellung als studentische Hilfskraft wurde von allen "
    "Kostenstellenverantwortlichen freigegeben.\n\n"
    "Bitte bestätigen Sie den Antrag unter folgendem Link:\n{acceptance_url}\n"
)
ACCEPTANCE_LINK_STUDENT_BODY_EN = (
    "Your application (Id: {petition_id}) for employment as a student assistant has been approved by all "
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
    "Der Kostenstellenverantwortliche {requesting_approver} hat eine Änderung an Ihrem Antrag (Id: {petition_id}) "
    "angefordert:\n\n"
    "{message}\n\n"
    "Bitte melden Sie sich an, um die Änderungen vorzunehmen.\n"
)
APPROVER_REVISION_SUPERVISOR_BODY_EN = (
    "The budget approver {requesting_approver} has requested changes to your application (Id: {petition_id}):\n\n"
    "{message}\n\n"
    "Please log in to make the requested changes.\n"
)
APPROVER_REVISION_APPROVER_BODY_DE = (
    "Der Kostenstellenverantwortliche {requesting_approver} hat eine Änderung an dem Antrag (Id: {petition_id}) "
    "angefordert:\n\n"
    "{message}\n\n"
    "Sie werden benachrichtigt, sobald die Änderungen vorgenommen wurden.\n"
)
APPROVER_REVISION_APPROVER_BODY_EN = (
    "The budget approver {requesting_approver} has requested changes to application (Id: {petition_id}):\n\n"
    "{message}\n\n"
    "You will be notified once the changes have been made.\n"
)

# --- Budget position rejected -------------------------------------------------

BUDGET_REJECTED_SUBJECT = "[ClockWork] Antrag abgelehnt / Application rejected"

# Placeholders: {rejecting_approver}
BUDGET_REJECTED_SUPERVISOR_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) wurde von dem Kostenstellenverantwortlichen {rejecting_approver} abgelehnt."
)
BUDGET_REJECTED_SUPERVISOR_BODY_EN = (
    "Your application (Id: {petition_id}) has been rejected by the budget approver {rejecting_approver}."
)
BUDGET_REJECTED_APPROVER_BODY_DE = (
    "Der Antrag (Id: {petition_id}) wurde von dem Kostenstellenverantwortlichen {rejecting_approver} abgelehnt."
)
BUDGET_REJECTED_APPROVER_BODY_EN = (
    "The application (Id: {petition_id}) has been rejected by the budget approver {rejecting_approver}."
)

# --- Petition updated by the supervisor ---------------------------------------

PETITION_UPDATED_SUBJECT = "[ClockWork] Antrag aktualisiert / Application updated"

# Placeholders: {approval_url}
PETITION_UPDATED_APPROVER_BODY_DE = (
    "Der Antrag (Id: {petition_id}) wurde aktualisiert.\n\n"
    "Bitte überprüfen Sie die Änderungen und geben Sie Ihre Freigabe unter folgendem Link:\n{approval_url}\n"
)
PETITION_UPDATED_APPROVER_BODY_EN = (
    "Application (Id: {petition_id}) has been updated.\n\n"
    "Please review the changes and provide your approval at the following link:\n{approval_url}\n"
)

# --- Student accepted the petition --------------------------------------------

STUDENT_ACCEPTED_SUPERVISOR_SUBJECT = "[ClockWork] Student hat zugestimmt / Student accepted"
STUDENT_ACCEPTED_SUPERVISOR_BODY_DE = (
    "Die studentische Hilfskraft hat dem Antrag (Id: {petition_id}) zugestimmt.\n\n"
    "Der Antrag wird nun von PersonalServices bearbeitet."
)
STUDENT_ACCEPTED_SUPERVISOR_BODY_EN = (
    "The student assistant has accepted application (Id: {petition_id}).\n\n"
    "The application will now be processed by PersonalServices."
)

# --- Student rejected the petition --------------------------------------------

STUDENT_REJECTED_SUBJECT = "[ClockWork] Student hat abgelehnt / Student rejected"
STUDENT_REJECTED_SUPERVISOR_BODY_DE = (
    "Die studentische Hilfskraft hat den Antrag (Id: {petition_id}) abgelehnt.\n\n"
    "Bitte setzen Sie sich mit der studentischen Hilfskraft in Verbindung."
)
STUDENT_REJECTED_SUPERVISOR_BODY_EN = (
    "The student assistant has rejected application (Id: {petition_id}).\n\n"
    "Please contact the student assistant."
)
STUDENT_REJECTED_APPROVER_BODY_DE = (
    "Die studentische Hilfskraft hat den Antrag (Id: {petition_id}) abgelehnt.\n\n"
    "Der Antrag wird nicht weiter bearbeitet."
)
STUDENT_REJECTED_APPROVER_BODY_EN = (
    "The student assistant has rejected application (Id: {petition_id}).\n\n"
    "The application will not be processed further."
)

# --- Revision requested by the student ----------------------------------------

# Placeholders: {message}
STUDENT_REVISION_SUPERVISOR_BODY_DE = (
    "Die studentische Hilfskraft hat eine Änderung an dem Antrag (Id: {petition_id}) angefordert:\n\n"
    "{message}\n\n"
    "Bitte melden Sie sich an, um die Änderungen vorzunehmen."
)
STUDENT_REVISION_SUPERVISOR_BODY_EN = (
    "The student assistant has requested changes to application (Id: {petition_id}):\n\n"
    "{message}\n\n"
    "Please log in to make the requested changes."
)

# --- Clerk approved the petition ----------------------------------------------

CONTRACT_STUDENT_SUBJECT = "[ClockWork] Arbeitsvertrag / Employment contract"
CONTRACT_STUDENT_BODY_DE = (
    "Anbei finden Sie Ihren Arbeitsvertrag für den Antrag (Id: {petition_id}).\n\n"
    "Bitte drucken Sie den Vertrag aus, unterschreiben Sie ihn und reichen Sie ihn bei PersonalServices ein."
)
CONTRACT_STUDENT_BODY_EN = (
    "Please find attached your employment contract for application (Id: {petition_id}).\n\n"
    "Please print the contract, sign it and submit it to PersonalServices."
)

CLERK_APPROVED_SUBJECT = "[ClockWork] Neuer Antragstatus / Application status update"
CLERK_APPROVED_SUPERVISOR_BODY_DE = (
    "Der Antrag (Id: {petition_id}) wurde von PersonalServices freigegeben.\n\n"
    "Bitte melden Sie sich an, um den Antragsstatus zu überprüfen."
)
CLERK_APPROVED_SUPERVISOR_BODY_EN = (
    "Your application (Id: {petition_id}) has been approved by PersonalServices.\n\n"
    "Please log in and review the application's status."
)
CLERK_APPROVED_APPROVER_BODY_DE = "Der Antrag (Id: {petition_id}) wurde von PersonalServices freigegeben."
CLERK_APPROVED_APPROVER_BODY_EN = "The application (Id: {petition_id}) has been approved by PersonalServices."

# --- Revision requested by the clerk ------------------------------------------

# Placeholders: {message}
CLERK_REVISION_STUDENT_BODY_DE = (
    "PersonalServices hat eine Anpassung Ihrer Angaben / Unterlagen angefordert:\n\n"
    "{message}\n\n"
    "Bitte melden Sie sich an, um Ihre Angaben zu prüfen und zu ergänzen."
)
CLERK_REVISION_STUDENT_BODY_EN = (
    "PersonalServices has requested a revision of your data / documents:\n\n"
    "{message}\n\n"
    "Please log in to review and amend your personal information or documents."
)

# --- Petition completed by the clerk ------------------------------------------

PETITION_COMPLETED_SUBJECT = "[ClockWork] Einstellung abgeschlossen / Employment process completed"
PETITION_COMPLETED_STUDENT_BODY_DE = (
    "Ihre Einstellung (Antrag (Id: {petition_id})) ist abgeschlossen.\n\n"
    "Willkommen als Beschäftigte*r der Goethe-Universität!"
)
PETITION_COMPLETED_STUDENT_BODY_EN = (
    "Your employment (application ID (Id: {petition_id})) has been completed.\n\n"
    " Welcome as employee of Goethe University!"
)
PETITION_COMPLETED_SUPERVISOR_BODY_DE = (
    "Der Antrag (Id: {petition_id}) auf Einstellung einer studentischen Hilfskraft ist abgeschlossen.\n\n"
    "\nSie erhalten demnächst den unterschriebenen Arbeitsvertrag von PersonalServices. Bitte geben Sie diesen "
    "an die studentische Hilfskraft weiter."
)
PETITION_COMPLETED_SUPERVISOR_BODY_EN = (
    "Application (Id: {petition_id}) for the employment of a student assistant has been completed.\n\n"
    "In a few days, you will be receiving the employment contract from PersonalServices. Please hand it over "
    "to the student assistant."
)

# --- Petition deleted by the clerk --------------------------------------------

PETITION_DELETED_SUBJECT = "[ClockWork] Antrag gelöscht / Application deleted"

# Optional reason, appended to the bodies below via {reason_text} / {reason_text_en}. Placeholders: {reason}
DELETION_REASON_DE = "\n\nBegründung:\n{reason}"
DELETION_REASON_EN = "\n\nReason:\n{reason}"

# Placeholders: {reason_text}, {reason_text_en}
PETITION_DELETED_SUPERVISOR_BODY_DE = "Ihr Antrag (Id: {petition_id}) wurde von PersonalServices gelöscht.{reason_text}"
PETITION_DELETED_SUPERVISOR_BODY_EN = (
    "Your application (Id: {petition_id}) has been deleted by PersonalServices.{reason_text_en}"
)
PETITION_DELETED_STUDENT_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) zur Einstellung als studentische Hilfskraft wurde von PersonalServices "
    "gelöscht.{reason_text}"
)
PETITION_DELETED_STUDENT_BODY_EN = (
    "Your application (Id: {petition_id}) for employment as a student assistant has been deleted by "
    "PersonalServices.{reason_text_en}"
)
PETITION_DELETED_APPROVER_BODY_DE = "Der Antrag (Id: {petition_id}) wurde von PersonalServices gelöscht.{reason_text}"
PETITION_DELETED_APPROVER_BODY_EN = (
    "The application (Id: {petition_id}) has been deleted by PersonalServices.{reason_text_en}"
)
