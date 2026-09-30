import io
from pdf2image import convert_from_bytes
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image

from api.redactor.dob import redact_image_with_pii_dob
# from api.redactor.pii import redact_image_with_pii
from api.redactor.aadhar_card_no import redact_image_with_aadhar_card_no
from api.redactor.address import redact_address_from_image
from api.redactor.driving_licence_no import redact_image_with_driving_licence_no
# from api.redactor.signature import redact_signatures_from_image
from api.redactor.mobile_number import redact_image_with_mobile_number
from api.redactor.pan_card_no import redact_image_with_pan_card_no

def redact_pdf_with_pii(pdf_bytes: bytes) -> bytes:
    redacted_images = []
    images = convert_from_bytes(pdf_bytes)

    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        redacted_pii = redact_image_with_pii_dob(buf.getvalue())
        # redacted_pii = redact_image_with_pii(redacted_pii)
        redacted_pii = redact_address_from_image(redacted_pii)
        redacted_pii = redact_image_with_aadhar_card_no(redacted_pii)
        redacted_pii = redact_image_with_pan_card_no(redacted_pii)
        redacted_pii = redact_image_with_driving_licence_no(redacted_pii)
        redacted_pii = redact_image_with_mobile_number(redacted_pii)
        # redacted_pii = redact_signatures_from_image(redacted_pii)
        redacted_images.append(Image.open(io.BytesIO(redacted_pii)))
        

    out_buf = io.BytesIO()
    c = canvas.Canvas(out_buf, pagesize=A4)

    for img in redacted_images:
        img_width, img_height = img.size
        aspect = img_height / float(img_width)
        new_width = A4[0]
        new_height = new_width * aspect

        img_reader = ImageReader(img)
        c.drawImage(img_reader, 0, A4[1] - new_height, width=new_width, height=new_height)
        c.showPage()

    c.save()
    out_buf.seek(0)
    return out_buf.read()
