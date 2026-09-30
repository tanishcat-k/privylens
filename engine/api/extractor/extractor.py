from api.redactor.dob import redact_image_with_pii_dob
from api.redactor.driving_licence_no import redact_image_with_driving_licence_no
from api.redactor.aadhar_card_no import redact_image_with_aadhar_card_no
# from api.redactor.pii import redact_image_with_pii
from api.redactor.address import redact_address_from_image
from api.redactor.pan_card_no import redact_image_with_pan_card_no
from api.redactor.mobile_number import redact_image_with_mobile_number
from api.redactor.email import redact_image_with_email
from api.redactor.vid import redact_image_with_vid
from .pdf_format import redact_pdf_with_pii
from .docx_format import redact_docx_with_pii

def redact_file_with_format(filename: str, file_bytes: bytes):
    ext = filename.lower().split('.')[-1]
    if ext == "pdf":
        return redact_pdf_with_pii(file_bytes), "application/pdf", "pdf"
    elif ext == "docx":
        return redact_docx_with_pii(file_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"
    elif ext in ["png", "jpg", "jpeg"]:
        processed_image = redact_image_with_pii_dob(file_bytes)
        processed_image = redact_image_with_aadhar_card_no(processed_image)
        processed_image = redact_image_with_driving_licence_no(processed_image)
        processed_image = redact_image_with_pan_card_no(processed_image)
        processed_image = redact_image_with_vid(processed_image)
        processed_image = redact_image_with_email(processed_image)
        # processed_image = redact_image_with_pii(processed_image)
        processed_image = redact_address_from_image(processed_image)
        processed_image = redact_image_with_mobile_number(processed_image)
        # processed_image = redact_signatures_from_image(processed_image)
        return processed_image, "image/png", "png"
    else:
        raise ValueError("Unsupported file format")




