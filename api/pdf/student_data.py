from datetime import date
from io import BytesIO

from pikepdf import Dictionary, Name, String
from pikepdf.form import ExtendedAppearanceStreamGenerator, Form, Pdf

import api.consts as consts
from api.db.schema.employee import Gender
from api.pydantic_models import EmployeeRead, PetitionRead


def create_student_data_pdf(employee: EmployeeRead) -> BytesIO:
    if not employee:
        raise ValueError("Employee data is missing")

    buffer = BytesIO()

    try:
        with Pdf.open(
            "".join([consts.PDF_TEMPLATE_DIR, consts.PERSONAL_DATA_PDF_TEMPLATE])
        ) as pdf:
            af = pdf.Root.get("/AcroForm", None)
            if af is None:
                af = pdf.make_indirect(Dictionary())
                pdf.Root.AcroForm = af
            # Don't set NeedAppearances - we're setting appearance states manually
            # Provide a default appearance (font tag + size + black color)
            af["/DA"] = String("/Helv 11 Tf 0 g")
            form = Form(pdf, ExtendedAppearanceStreamGenerator)

            def safe_set_field(field_name: str, value: str):
                if field_name in form:
                    form[field_name].value = value

            def safe_set_checkbox(field_name: str, checked: bool = True):
                if field_name in form:
                    form[field_name].checked = checked

            # Dictionary mapping PDF fields to EmployeeRead attributes
            # Format: "PDF_Field_Name": "employee_attribute_name"
            simple_fields = {
                "Nachname": "last_name",
                "Vorname": "first_name",
                "Geburtsort": "city_of_birth",
                "Krankenkasse": "health_insurance",
                "Staatsangehörigkeit": "nationality",
                "PLZ_Wohnort": "postal_code",
                "Adresse": "address",
                "Email": "user_email",
                "Name der Bank": "bank_name",
                "Text7": "bic",  # BIC field is labeled as "Text7"
            }

            # Process simple string fields - accessing attributes safely
            for pdf_field, attr_name in simple_fields.items():
                value = getattr(employee, attr_name, None)
                if value:
                    safe_set_field(pdf_field, value)

            # Process fields with specific formatting or logic
            # Date of Birth
            dob = getattr(employee, "date_of_birth", None)
            if dob:
                safe_set_field("Geburtsdatum", dob.strftime("%d.%m.%Y"))

            # Marital Status
            married = getattr(employee, "married", None)
            if married is not None:
                safe_set_field("Familienstand", "verheiratet" if married else "ledig")

            # Telephone - same value for Telefon and Mobil
            phone = getattr(employee, "telephone_number", None)
            if phone:
                safe_set_field("Telefon", phone)
                safe_set_field("Mobil", phone)

            # Account Holder Name (First + Last)
            first = getattr(employee, "first_name", "")
            last = getattr(employee, "last_name", "")
            if first and last:
                safe_set_field("Kontoinhaberin", f"{first} {last}")

            # Gender Checkboxes
            gender = getattr(employee, "gender", None)
            if gender:
                if gender == Gender.FEMALE:
                    safe_set_checkbox("weiblich", True)
                elif gender == Gender.MALE:
                    safe_set_checkbox("männlich", True)
                elif gender == Gender.OTHER:
                    safe_set_checkbox("divers", True)
                else:
                    safe_set_checkbox("keine Angabe", True)

            # Previous Employment
            prev_employed = getattr(employee, "previously_employed", None)
            if prev_employed is not None:
                if prev_employed:
                    safe_set_checkbox("ja Zeitraum", True)
                    duration = getattr(employee, "prev_emp_duration", None)
                    if duration:
                        safe_set_field("Zeitraum", duration)
                else:
                    safe_set_checkbox("nein", True)

            # IBAN (Preserving logic as requested)
            iban_val = getattr(employee, "iban", None)
            if iban_val:
                # Split IBAN into segments (assuming German IBAN format)
                iban = iban_val.replace(" ", "")  # Remove any spaces
                # German IBAN: DE + 2 digits + bank code (8 digits) + account number (10 digits) = 22 chars
                # IBAN format for the 6 fields: each field should be 4 characters
                if len(iban) >= 4:
                    safe_set_field("IBAN_1", iban[0:4])  # First 4 chars
                if len(iban) >= 8:
                    safe_set_field("IBAN_2", iban[4:8])  # Next 4 chars
                if len(iban) >= 12:
                    safe_set_field("IBAN_3", iban[8:12])  # Next 4 chars
                if len(iban) >= 16:
                    safe_set_field("IBAN_4", iban[12:16])  # Next 4 chars
                if len(iban) >= 20:
                    safe_set_field("IBAN_5", iban[16:20])  # Next 4 chars
                if len(iban) >= 22:
                    safe_set_field("IBAN_6", iban[20:])  # Remaining chars

            student_username = getattr(employee, "username", None)
            if student_username:
                safe_set_field("Name Vorname", student_username)

            # Fill current date
            safe_set_field("Frankfurt den", date.today().strftime("%d.%m.%Y"))

            # Set NeedAppearances to True so PDF viewers regenerate the appearance streams
            if "/AcroForm" in pdf.Root:
                pdf.Root["/AcroForm"]["/NeedAppearances"] = True

            pdf.save(buffer, normalize_content=True)

    except Exception as e:
        # Catch errors to prevent raw 500 crashes and provide meaningful context
        raise ValueError(f"Error generating Student Data PDF: {str(e)}")

    buffer.seek(0)
    return buffer
