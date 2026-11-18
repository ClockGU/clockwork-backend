"""
Subjects and bodies of all mails sent by the EmailHandler.

Bodies are str.format templates, rendered by EmailHandler._render_body, which
appends the footer and joins the German and English part with the separator.
Placeholders available in every body: (Id: {petition_id}), {support_mail}, {frontend_url}.
Any other placeholder must be passed by the sending method.
"""

SEPARATOR = "\n\n--------------\n\n"

FOOTER_DE = (
    "\nSie erhalten diese Mail im Rahmen des SHK-Einstellungsprozesses der Software ClockWork. "
    "Bei Fragen oder Problemen wenden Sie sich bitte an {support_mail}.\n"
)

FOOTER_EN = (
    "\nYou are receiving this email as part of student employment process of the software, ClockWork. "
    "If you have any questions or encounter any problems, please email {support_mail}.\n"
)

# --- Petition created ---------------------------------------------------------

PETITION_CREATED_STUDENT_SUBJECT = "[ClockWork] Neuer Antrag erstellt / New hiring petition created"
PETITION_CREATED_STUDENT_BODY_DE = (
    "Es wurde ein Antrag auf Einstellung (Id: {petition_id}) als studentische Hilfskraft für Sie gestellt.\n"
    "Der Antrag wird nun von den Kostenstellenverantwortlichen geprüft.\n"
    "Nach dieser Prüfung werden Sie über weitere Schritte informiert.\n"
)
PETITION_CREATED_STUDENT_BODY_EN = (
    "A hiring petition (Id: {petition_id}) for employment as student assistant has been submitted for you.\n"
    "The petition is currently reviewed by the budget approvers.\n"
    "You will be informed about further steps after successful approval by the budget approvers \n"
)

# Placeholders: {budget_position}, {approval_url}
APPROVAL_REQUEST_APPROVER_SUBJECT = (
    "[ClockWork] Neue Antragsgenehmigung / New approval request"
)
APPROVAL_REQUEST_APPROVER_BODY_DE = (
    "Sie haben einen neuen Antrag für die Einstellung einer studentischen Hilfskraft auf die Kostenstelle\n"
    "{budget_position} erhalten und müssen diesen freigeben.\n\n"
    "Mit diesem Link gelangen Sie zum Antrag und können diesen genehmigen, ablehnen oder eine Änderung\n"
    "anfordern: {approval_url}\n\n"
    "Der Link ist ohne Passwortauthentifizierung zugänglich und somit vertraulich zu behandeln.\n"
)
APPROVAL_REQUEST_APPROVER_BODY_EN = (
    "You received an approval request for the employment of a new student assistant on the budget position\n"
    "{budget_position}.\n\n"
    "The the submitted hiring petition is accessible via this link where you can either approve or reject the petition or\n"
    "request changes: {approval_url}\n\n"
    "The Link is accessible without any authentication and thereby confidential.\n"
)

# --- Budget approved (all budget positions) -----------------------------------

BUDGET_APPROVED_SUBJECT = "[ClockWork] Kostenstelle(n) freigegeben / Budget approver(s) approved"
BUDGET_APPROVED_SUPERVISOR_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) für die Einstellung einer studentischen Hilfskraft wurde von allen"
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
    "Der Antrag (Id: {petition_id}) für Ihre Einstellung als studentische Hilfskraft wurde von allen\n"
    "Kostenstellenverantwortlichen freigegeben.\n\n"
    "Unter folgendem Link können Sie den Antrag annehmen oder ablehnen:\n{acceptance_url}\n"
)
ACCEPTANCE_LINK_STUDENT_BODY_EN = (
    "The hiring petition (Id: {petition_id}) for your employment as a student assistant has been approved by all\n"
    "budget approvers.\n\n"
    "Please accept or decline the hiring petition at the following link:\n{acceptance_url}\n"
)

# Placeholders: {dashboard_url}
UPLOAD_REQUEST_STUDENT_SUBJECT = "[ClockWork] Dokumente hochladen / Upload Documents"
UPLOAD_REQUEST_STUDENT_BODY_DE = (
    "Der Antrag (Id: {petition_id}) für Ihre Einstellung als studentische Hilfskraft wurde von allen\n"
    "Kostenstellenverantwortlichen freigegeben.\n\n"
    "Füllen Sie nun alle nötigen persönlichen Daten aus und laden die notwendigen Unterlagen hoch.\n"
    "Benötigt werden\n\n"
    "- Selbstauskunft zur Lohnsteuererklärung (ELStAM)\n"
    "- Fragebogen zur Sozialversicherung\n"
    "- aktuelle Studienbescheinigung\n"
    "- Mitgliedsbescheinigung Ihrer Krankenkasse\n\n"
    "Das Dashboard ist unter folgendem Link erreichbar: {dashboard_url}\n"
)
UPLOAD_REQUEST_STUDENT_BODY_EN = (
    "The hiring petition (Id: {petition_id}) for your employment as a student assistant has been approved by all "
    "budget approvers.\n\n"
    "Please fill out all required personal data and upload all required files.\n"
    "Required files are:"
    "- Self-disclosure form for income tax (ELStAM form)\n"
    "- Social Security questionnaire\n"
    "- current certificate of enrolment\n"
    "- Health insurance membership certificate\n\n"
    "The dashboard can be accessed from this link: {dashboard_url}\n"
)

# --- Revision requested (shared default subject) ------------------------------

REVISION_REQUESTED_SUBJECT = "[ClockWork] Änderungen angefordert / Changes requested"

# --- Revision requested by a budget approver ----------------------------------

NO_REVISION_MESSAGE = "No specific message provided."

# Placeholders: {requesting_approver}, {message}
APPROVER_REVISION_SUPERVISOR_BODY_DE = (
    "Ein*e Kostenstellenverantwortliche*r (E-Mail: {requesting_approver}) hat eine Änderung an Ihrem Antrag (Id: {petition_id}) "
    "angefordert:\n\n"
    "{message}\n\n"
    "Bitte melden Sie sich an um Änderungen an dem Antrag vorzunehmen oder diesen zu löschen.\n"
)
APPROVER_REVISION_SUPERVISOR_BODY_EN = (
    "A budget approver (E-Mail: {requesting_approver}) has requested changes to your application (Id: {petition_id}):\n\n"
    "{message}\n\n"
    "Please log in to make changes to the petition or to delete it.\n"
)
APPROVER_REVISION_APPROVER_BODY_DE = (
    "Ein*e Kostenstellenverantwortliche*r (E-Mail: {requesting_approver}) hat eine Änderung an dem Antrag (Id: {petition_id}) "
    "angefordert:\n\n"
    "{message}\n\n"
    "Sie werden benachrichtigt, sobald die Änderungen vorgenommen wurden und der Antrag erneut eingereicht wird.\n"
    "Sofern Sie den Antrag noch nicht genehmigt haben ist der Link den Sie erhalten haben hiermit ungültig.\n"
)
APPROVER_REVISION_APPROVER_BODY_EN = (
    "A budget approver (E-Mail: {requesting_approver}) has requested changes to application (Id: {petition_id}):\n\n"
    "{message}\n\n"
    "You will be notified once the changes have been made and the petition is re-submitted.\n"
    "In case you have not yet approved the petition the link you received is hereby invalid.\n"
)

# --- Budget position rejected -------------------------------------------------

BUDGET_REJECTED_SUBJECT = "[ClockWork] Antrag abgelehnt / Petition rejected"

# Placeholders: {rejecting_approver}
BUDGET_REJECTED_SUPERVISOR_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) wurde von dem*der Kostenstellenverantwortlichen (E-Mail: {rejecting_approver})\n"
    "endgültig abgelehnt und dadurch gelöscht."
)
BUDGET_REJECTED_SUPERVISOR_BODY_EN = (
    "Your petition (Id: {petition_id}) has been rejected by the budget approver (E-Mail: {rejecting_approver})\n"
    "and has consequently been deleted."
)
BUDGET_REJECTED_APPROVER_BODY_DE = (
    "Der Antrag (Id: {petition_id}) wurde von einer*einem anderen Kostenstellenverantwortlichen\n"
    "endgültig abgelehnt und dadurch gelöscht.\n"
    "Falls Sie den Antrag bereits zu gestimmt haben:\n"
    "Sie hatten für diesen Antrag ursprünglich eine Finanzierung von {hours}h zu {percentage}% zugesagt.\n"
    'Dieses Budget ist nun wieder "frei".\n'
)
BUDGET_REJECTED_APPROVER_BODY_EN = (
    "The petition (Id: {petition_id}) has been rejected by the budget approver\n"
    "and has consequently been deleted.\n"
    "In case you already approved this petition:\n"
    "You approved a budget of {hours}h for {percentage}% for this hiring petition.\n"
    'This budget is now "freed" again.\n'
)

# --- Petition updated by the supervisor ---------------------------------------

PETITION_UPDATED_SUBJECT = "[ClockWork] Antrag aktualisiert / Petition updated"

# Placeholders: {approval_url}
PETITION_UPDATED_APPROVER_BODY_DE = (
    "Der Antrag (Id: {petition_id}) wurde aktualisiert.\n\n"
    "Bitte überprüfen Sie die Änderungen und geben Sie Ihre Freigabe unter folgendem Link:\n"
    "{approval_url}\n"
)
PETITION_UPDATED_APPROVER_BODY_EN = (
    "The petition (Id: {petition_id}) has been updated.\n\n"
    "Please review the changes and approve them at the following link:\n"
    "{approval_url}\n"
)

# --- Student accepted the petition --------------------------------------------

STUDENT_ACCEPTED_SUPERVISOR_SUBJECT = "[ClockWork] Studierende*r hat zugestimmt / Student accepted"
STUDENT_ACCEPTED_SUPERVISOR_BODY_DE = (
    "Der*Die Studierende hat dem Antrag (Id: {petition_id}) zugestimmt.\n\n"
    "Der Antrag wird nun von Team-Hilfskräfte (HR-PS) bearbeitet."
)
STUDENT_ACCEPTED_SUPERVISOR_BODY_EN = (
    "The student has accepted application (Id: {petition_id}).\n\n"
    "The application will now be processed by the Team-Hilfskräfte (HR-PS)."
)

# --- Student rejected the petition --------------------------------------------

STUDENT_REJECTED_SUBJECT = "[ClockWork] Studierende*r hat abgelehnt / Student rejected"
STUDENT_REJECTED_SUPERVISOR_BODY_DE = (
    "Der*Die Studierende hat den Antrag (Id: {petition_id}) abgelehnt.\n"
    "Der Antrag wurde dadurch gelöscht.\n\n"
    "Bitte setzen Sie sich mit dem*der Studierenden in Verbindung falls Klärungsbedarf besteht."
)
STUDENT_REJECTED_SUPERVISOR_BODY_EN = (
    "The student has rejected the petition (Id: {petition_id}).\n"
    "The petition was deleted by this action.\n\n"
    "Please contact the student assistant if clarification is needed."
)
STUDENT_REJECTED_APPROVER_BODY_DE = (
    "Der*Die Studierende hat den Antrag (Id: {petition_id}) abgelehnt.\n\n"
    "Der Antrag wird dadurch gelöscht und nicht weiter bearbeitet.\n"
    "Sie hatten für diesen Antrag ursprünglich eine Finanzierung von {hours}h zu {percentage}% zugesagt.\n"
    "Dieses Budget ist nun wieder \"frei\".\n"
)
STUDENT_REJECTED_APPROVER_BODY_EN = (
    "The student assistant has rejected the petition (Id: {petition_id}).\n\n"
    "The application was thereby deleted and will not be processed further.\n"
    "You approved a budget of {hours}h for {percentage}% for this hiring petition.\n"
    "This budget is now \"freed\" again.\n"
)

# --- Revision requested by the student ----------------------------------------

# Placeholders: {message}
STUDENT_REVISION_SUPERVISOR_BODY_DE = (
    "Der*Die Studierende hat eine Änderung an dem Antrag (Id: {petition_id}) angefordert:\n\n"
    "{message}\n\n"
    "Bitte melden Sie sich an, um die Änderungen vorzunehmen oder nehmen Sie Kontakt zu dem*der Studierenden auf.\n"
)
STUDENT_REVISION_SUPERVISOR_BODY_EN = (
    "The student has requested changes to the petition (Id: {petition_id}):\n\n"
    "{message}\n\n"
    "Please log in to make the requested changes or contact the student.\n"
)

# --- Clerk approved the petition ----------------------------------------------

CONTRACT_STUDENT_SUBJECT = "[ClockWork] Arbeitsvertrag / Employment contract"
CONTRACT_STUDENT_BODY_DE = (
    "Anbei finden Sie Ihren Arbeitsvertrag für den Antrag (Id: {petition_id}).\n\n"
    "Bitte drucken Sie den Vertrag ZWEIFACH aus, unterschreiben Sie BEIDE EXEMPLARE und reichen Sie ihn bei PersonalServices ein.\n"
    "Sie können die unterschriebenen Verträge per Hauspost versenden. Hierzu legen Sie BEIDE UNTERSCHRIEBENEN EXEMPLARE\n"
    "in eine Briefumschlag, verschließen diesen und beschriften ihn mit:\n"
    "HR-PS Team-Hilfskräfte\n"
    "Theodor-W.-Adorno-Platz 1\n"
    "60323 Frankfurt am Main \n\n"
    "Den so beschrifteten Briefumschlag können Sie bei jedem*jeder Pförtner*in der Universität mit den Worten\n"
    "'Zur Versendung per Hauspost bitte.' abgeben.\n\n"
    "Andernfalls: Können Sie den Brief auch entsprechend frankieren und auf dem regulären Postweg versenden\n."
)
CONTRACT_STUDENT_BODY_EN = (
    "Please find attached your employment contract for application (Id: {petition_id}).\n\n"
    "Print the contract TWICE, sign BOTH EXEMPLARS and submit it to PersonalServices.\n"
    "You can send the signed contracts via the house post system. In order to do so place BOTH SIGNED EXEMPLARS\n"
    "in an envelop, close it and label it with the following address:\n"
    "HR-PS Team-Hilfskräfte\n"
    "Theodor-W.-Adorno-Platz 1\n"
    "60323 Frankfurt am Main \n\n"
    "The labeled envelop can then be handed over to any porter at the university with the phrase 'For sending via house post please'\n"
    "(It may be advisable to use the German phrase above in cases of communication issues).\n\n"
    "Otherwise: Apply sufficient post-stamps to the envelop and send it via regular post.\n"
)

CLERK_APPROVED_SUBJECT = "[ClockWork] Neuer Antragsstatus / Application status update"
CLERK_APPROVED_SUPERVISOR_BODY_DE = (
    "Der Antrag (Id: {petition_id}) wurde von PersonalServices freigegeben.\n\n"
    "Der*Die Studierende hat die Vertragsunterlagen erhalten und muss diese nun\n"
    "unterschrieben beim Team-Hilfskräfte einreichen.\n"
    " Sie werden benachrichtigt sobald das Team-Hilfskräfte die Vertragsdokumente erhalten\n"
    "und bearbeitet hat.\n"
)
CLERK_APPROVED_SUPERVISOR_BODY_EN = (
    "Your application (Id: {petition_id}) has been approved by PersonalServices.\n\n"
    "The student received the contract documents and has to submit them to the Team-Hilfskräfte\n"
    "signed. You will be notified as soon as the Team-Hilfskräfte has received and\n"
    "processed the contract documents.\n"
)
CLERK_APPROVED_APPROVER_BODY_DE = "Der Antrag (Id: {petition_id}) wurde von PersonalServices freigegeben."
CLERK_APPROVED_APPROVER_BODY_EN = "The application (Id: {petition_id}) has been approved by PersonalServices."

# --- Revision requested by the clerk ------------------------------------------

# Placeholders: {message}
CLERK_REVISION_STUDENT_BODY_DE = (
    "PersonalServices hat eine Anpassung Ihrer Angaben / Unterlagen angefordert:\n\n"
    "{message}\n\n"
    "Bitte melden Sie sich an, um Ihre Angaben zu prüfen und zu ergänzen.\n"
)
CLERK_REVISION_STUDENT_BODY_EN = (
    "PersonalServices has requested a revision of your data / documents:\n\n"
    "{message}\n\n"
    "Please log in to review and amend your personal information or documents.\n"
)

# --- Petition completed by the clerk ------------------------------------------

PETITION_COMPLETED_SUBJECT = "[ClockWork] Einstellung abgeschlossen / Employment process completed"
PETITION_COMPLETED_STUDENT_BODY_DE = (
    "Ihre Einstellung (Antrag (Id: {petition_id})) ist abgeschlossen.\n\n"
    "Willkommen als studentische Hilfskraft an der Goethe-Universität!\n"
)
PETITION_COMPLETED_STUDENT_BODY_EN = (
    "Your employment (application ID (Id: {petition_id})) has been completed.\n\n"
    "Welcome as student assistant of the Goethe University!\n"
)
PETITION_COMPLETED_SUPERVISOR_BODY_DE = (
    "Der Antrag (Id: {petition_id}) auf Einstellung einer studentischen Hilfskraft ist abgeschlossen.\n\n"
)
PETITION_COMPLETED_SUPERVISOR_BODY_EN = (
    "Petition (Id: {petition_id}) for the employment of a student assistant has been completed.\n\n"
)

# --- Petition deleted by the clerk --------------------------------------------

PETITION_DELETED_SUBJECT = "[ClockWork] Antrag gelöscht / Application deleted"

# Optional reason, appended to the bodies below via {reason_text} / {reason_text_en}. Placeholders: {reason}
DELETION_REASON_DE = "Begründung:\n{reason}"
DELETION_REASON_EN = "Reason:\n{reason}"

# Placeholders: {reason_text}, {reason_text_en}
PETITION_DELETED_SUPERVISOR_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) auf Einstellung einer studentischen Hilfskraft wurde von PersonalServices abgelehnt.\n\n"
    "{reason_text}\n\n"
    "Der Antrag wurde durch die Ablehnung gelöscht. Bitte treten Sie mit den Prozessbeteiligten\n"
    "in Kontakt um Unstimmigkeiten zu klären.\n"
    )
PETITION_DELETED_SUPERVISOR_BODY_EN = (
    "Your hiring petition (Id: {petition_id}) has been declined by PersonalServices.\n\n"
    "{reason_text_en}\n\n"
    "The petition was consequently deleted. Please contact everyone involved in the process to clear out any\n"
    "discrepancies.\n"
)
PETITION_DELETED_STUDENT_BODY_DE = (
    "Ihr Antrag (Id: {petition_id}) zur Einstellung als studentische Hilfskraft wurde von PersonalServices abgelehnt.\n\n"
    "{reason_text}\n\n"
    "Der Antrag wurde durch die Ablehnung gelöscht. Die Antragsteller*in wird vermutlich mit Ihnen in Kontakt treten\n"
    "um Unstimmigkeiten zu klären.\n"
)
PETITION_DELETED_STUDENT_BODY_EN = (
    "Your hiring petition (Id: {petition_id}) has been declined by PersonalServices.\n\n"
    "{reason_text_en}\n\n"
    "The petition was consequently deleted. The petitioner will probably contact you soon to clear out any discrepancies.\n"
)
PETITION_DELETED_APPROVER_BODY_DE = (
    "Der Antrag (Id: {petition_id}) auf Einstellung einer studentische Hilfskraft wurde von PersonalServices abgelehnt.\n\n"
    "{reason_text}\n\n"
    "Der Antrag wurde durch die Ablehnung gelöscht. Die Antragsteller*in wird vermutlich mit Ihnen in Kontakt treten\n"
    "um Unstimmigkeiten zu klären.\n"
)
PETITION_DELETED_APPROVER_BODY_EN = (
    "The hiring petition (Id: {petition_id}) has been declined by PersonalServices.\n\n"
    "{reason_text_en}\n\n"
    "The petition was consequently deleted. The petitioner will probably contact you soon to clear out any discrepancies.\n"
)
