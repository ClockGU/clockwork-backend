from io import BytesIO

from pikepdf.form import Form, Pdf, ExtendedAppearanceStreamGenerator
from pikepdf import Dictionary, String
import api.consts as consts

from api.pydantic_models import EmployeeRead, PetitionRead


def create_student_data_pdf(employee: EmployeeRead, petition: PetitionRead)-> BytesIO:
    buffer = BytesIO()
    with Pdf.open("".join([consts.PDF_TEMPLATE_DIR, consts.PERSONAL_DATA_PDF_TEMPLATE])) as pdf:
        af = pdf.Root.get("/AcroForm", None)
        if af is None:
            af = pdf.make_indirect(Dictionary())
            pdf.Root.AcroForm = af
        # Ask viewer to regenerate field appearances
        af["/NeedAppearances"] = True
        # Provide a default appearance (font tag + size + black color)
        af["/DA"] = String("/Helv 11 Tf 0 g")
        form = Form(pdf, ExtendedAppearanceStreamGenerator)
        # Intrspect all form field names with
        # print(filed[0] for field in form.fields.items())
        # ... add field population here ...
        # field["Name_of_field"].value = "value to set"

        pdf.save(buffer)
    buffer.seek(0)
    return buffer