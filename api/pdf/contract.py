from io import BytesIO
from uuid import uuid4

from pikepdf.form import Form, Pdf, ExtendedAppearanceStreamGenerator
from pikepdf import Dictionary, String
from datetime import date
import api.consts as consts

from api.pydantic_models import EmployeeRead, PetitionRead


def create_contract_pdf(employee: EmployeeRead, petition: PetitionRead)-> BytesIO:
    buffer = BytesIO()
    with Pdf.open("".join([consts.PDF_TEMPLATE_DIR, consts.CONTRACT_PDF_TEMPLATE])) as pdf:
        af = pdf.Root.get("/AcroForm", None)
        if af is None:
            af = pdf.make_indirect(Dictionary())
            pdf.Root.AcroForm = af
        # Ask viewer to regenerate field appearances
        af["/NeedAppearances"] = True
        # Provide a default appearance (font tag + size + black color)
        af["/DA"] = String("/Helv 11 Tf 0 g")
        form = Form(pdf, ExtendedAppearanceStreamGenerator)
        today = date.today()
        filename = f"Arbeitsvertrag_{employee.last_name}_{employee.first_name}_{today.strftime("%d-%m-%Y")}.pdf"

        form[consts.NAME_FIELD].value = f"{employee.last_name}, {employee.first_name}"
        form[consts.BIRTHDAY_FIELD].value = f"{employee.date_of_birth.strftime('%d.%m.%Y')}"
        form[consts.ADDRESS_FIELD].value = f"{employee.address},{employee.postal_code}"
        form[consts.CONTRACT_START_FIELD].value = f"{petition.start_date.strftime('%d.%m.%Y')}"
        form[consts.CONTRACT_END_FIELD].value = f"{petition.end_date.strftime('%d.%m.%Y')}"
        form[consts.DEBIT_WORKTIME_FIELD].value = f"{petition.minutes // 60}"
        form[consts.SIGNITURE_DATE_FIELD].value = today.strftime("%d.%m.%Y")
        pdf.save(buffer)
    buffer.seek(0)
    return buffer