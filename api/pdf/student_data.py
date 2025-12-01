from io import BytesIO
from datetime import date

from pikepdf.form import Form, Pdf, ExtendedAppearanceStreamGenerator
from pikepdf import Dictionary, String, Name
import api.consts as consts

from api.pydantic_models import EmployeeRead, PetitionRead


def create_student_data_pdf(employee: EmployeeRead, petition: PetitionRead)-> BytesIO:
    buffer = BytesIO()
    with Pdf.open("".join([consts.PDF_TEMPLATE_DIR, consts.PERSONAL_DATA_PDF_TEMPLATE])) as pdf:
        af = pdf.Root.get("/AcroForm", None)
        if af is None:
            af = pdf.make_indirect(Dictionary())
            pdf.Root.AcroForm = af
        # Don't set NeedAppearances - we're setting appearance states manually
        # Provide a default appearance (font tag + size + black color)
        af["/DA"] = String("/Helv 11 Tf 0 g")
        form = Form(pdf, ExtendedAppearanceStreamGenerator)
        

        
        # Helper function to safely set field values
        def safe_set_field(field_name: str, value: str):
            try:
                if field_name in form:
                    form[field_name].value = value
            except Exception as e:
                print(f"Warning: Could not set field '{field_name}': {e}", flush=True)
        
        # Helper function to safely set checkbox values  
        def safe_set_checkbox(field_name: str, checked: bool = True):
            try:
                if checked:
                    # form fields to implemented later
                    pass
            except Exception as e:
                print(f"Warning: Could not set checkbox '{field_name}': {e}", flush=True)
        
        # Fill employee personal data
        if employee.last_name:
            safe_set_field("Nachname", employee.last_name)
        if employee.first_name:
            safe_set_field("Vorname", employee.first_name)
        if employee.date_of_birth:
            safe_set_field("Geburtsdatum", employee.date_of_birth.strftime("%d.%m.%Y"))
        if employee.city_of_birth:
            safe_set_field("Geburtsort", employee.city_of_birth)
        if employee.married is not None:
            safe_set_field("Familienstand", "verheiratet" if employee.married else "ledig")
        if employee.health_insurance:
            safe_set_field("Krankenkasse", employee.health_insurance)
        if employee.nationality:
            safe_set_field("Staatsangehörigkeit", employee.nationality)
        if employee.postal_code:
            safe_set_field("PLZ_Wohnort", employee.postal_code)
        if employee.address:
            safe_set_field("Adresse", employee.address)
        if employee.user_email:
            safe_set_field("Email", employee.user_email)
        if employee.telephone_number:
            safe_set_field("Telefon", employee.telephone_number)
            safe_set_field("Mobil", employee.telephone_number)
        
        # Fill gender checkboxes
        if employee.gender:
            if employee.gender.lower() == "weiblich" or employee.gender.lower() == "female":
                safe_set_checkbox("weiblich", True)
            elif employee.gender.lower() == "männlich" or employee.gender.lower() == "male":
                safe_set_checkbox("männlich", True)
            elif employee.gender.lower() == "divers":
                safe_set_checkbox("divers", True)
            else:
                safe_set_checkbox("keine Angabe", True)
        
        # Fill previous employment information
        if employee.previously_employeed is not None:
            if employee.previously_employeed:
                safe_set_checkbox("ja Zeitraum", True)
                if employee.prev_emp_duration:
                    safe_set_field("Zeitraum", employee.prev_emp_duration)
            else:
                safe_set_checkbox("nein", True)
        
        # Fill bank account information
        if employee.first_name and employee.last_name:
            safe_set_field("Kontoinhaberin", f"{employee.first_name} {employee.last_name}")
        if employee.bank_name:
            safe_set_field("Name der Bank", employee.bank_name)
        if employee.bic:
            safe_set_field("Text7", employee.bic)  # BIC field is labeled as "Text7"
        if employee.iban:
            # Split IBAN into segments (assuming German IBAN format)
            iban = employee.iban.replace(" ", "")  # Remove any spaces
            # German IBAN: DE + 2 digits + bank code (8 digits) + account number (10 digits) = 22 chars
            # IBAN format for the 6 fields: each field should be 4 characters
            if len(iban) >= 4:
                safe_set_field("IBAN_1", iban[0:4])    # First 4 chars
            if len(iban) >= 8:
                safe_set_field("IBAN_2", iban[4:8])    # Next 4 chars
            if len(iban) >= 12:
                safe_set_field("IBAN_3", iban[8:12])   # Next 4 chars
            if len(iban) >= 16:
                safe_set_field("IBAN_4", iban[12:16])  # Next 4 chars
            if len(iban) >= 20:
                safe_set_field("IBAN_5", iban[16:20])  # Next 4 chars
            if len(iban) >= 22:
                safe_set_field("IBAN_6", iban[20:])    # Remaining chars
        
        # Fill student information from petition
        if hasattr(petition, 'student_username') and petition.student_username:
            safe_set_field("Name Vorname", petition.student_username)
        
        # Fill current date
        safe_set_field("Frankfurt den", date.today().strftime("%d.%m.%Y"))

        # Set NeedAppearances to True so PDF viewers regenerate the appearance streams
        if '/AcroForm' in pdf.Root:
            pdf.Root['/AcroForm']['/NeedAppearances'] = True

        pdf.save(buffer, normalize_content=True)
    buffer.seek(0)
    return buffer