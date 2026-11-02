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
