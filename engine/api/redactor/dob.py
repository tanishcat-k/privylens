from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from api.detector.dob import detect_pii_dob
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np
import cv2
import re





# ----------------------------------------------- #
# this redacts only dob in character form for day,month,year

# def redact_image_with_pii_dob(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))

#     # Brightness adjustment
#     np_image = np.array(image)
#     brightness = np.mean(np_image)
#     print(f"Brightness: {brightness}")
#     print(f"Original Resolution: {image.width}x{image.height}")

#     enhancer = ImageEnhance.Brightness(image)
#     if 175 <= brightness < 179:
#         image = enhancer.enhance(1.1)
#     elif brightness < 179:
#         image = enhancer.enhance(1.3)
#     elif 205 <= brightness <= 215:
#         image = enhancer.enhance(0.95)
#     elif 215 < brightness <= 225:
#         image = enhancer.enhance(0.9)
#     elif brightness > 225:
#         image = enhancer.enhance(0.85)

#     np_image = np.array(image)
#     brightness = np.mean(np_image)
#     print(f"New Brightness: {brightness}")

#     draw = ImageDraw.Draw(image)
#     width, height = image.size

#     # Get line-level OCR data
#     data = pytesseract.image_to_data(
#         image, 
#         output_type=pytesseract.Output.DICT, 
#         config="--oem 1"
#     )

#     # Get all character boxes
#     char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
#     char_positions = []
#     for b in char_boxes.splitlines():
#         ch, x1, y1, x2, y2, _ = b.split()
#         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#         # Convert coordinates
#         y1_pil = height - y2
#         y2_pil = height - y1
#         char_positions.append((ch, x1, y1_pil, x2, y2_pil))

#     # Loop through OCR lines
#     n_boxes = len(data['level'])
#     for i in range(n_boxes):
#         text = data['text'][i].strip()
#         if text and float(data['conf'][i]) > 10:
#             if detect_pii_dob(text)['contains_pii_dob']:
#                 print(f"PII DOB Detected in Line: {text}")
#                 # Bounding box for this line
#                 x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#                 # Redact all characters inside this line's bounding box
#                 for ch, cx1, cy1, cx2, cy2 in char_positions:
#                     if (cx1 >= x and cx2 <= x + w) and (cy1 >= y and cy2 <= y + h):
#                         draw.rectangle([cx1, cy1, cx2, cy2], fill="black")

#     # Save and return
#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()


# --------------------------------------------- #
# this redacts only dob based on character - day, month
def redact_image_with_pii_dob(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))

    # Brightness adjustment
    np_image = np.array(image)
    brightness = np.mean(np_image)
    print(f"Brightness: {brightness}")
    print(f"Original Resolution: {image.width}x{image.height}")

    enhancer = ImageEnhance.Brightness(image)
    if 175 <= brightness < 179:
        image = enhancer.enhance(1.1)
    elif brightness < 179:
        image = enhancer.enhance(1.3)
    elif 205 <= brightness <= 215:
        image = enhancer.enhance(0.95)
    elif 215 < brightness <= 225:
        image = enhancer.enhance(0.9)
    elif brightness > 225:
        image = enhancer.enhance(0.85)

    np_image = np.array(image)
    brightness = np.mean(np_image)
    print(f"New Brightness: {brightness}")

    draw = ImageDraw.Draw(image)
    width, height = image.size

    # OCR line-level
    data = pytesseract.image_to_data(
        image, 
        output_type=pytesseract.Output.DICT, 
        config="--oem 1"
    )

    # OCR character-level
    char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
    char_positions = []
    for b in char_boxes.splitlines():
        ch, x1, y1, x2, y2, _ = b.split()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        y1_pil = height - y2
        y2_pil = height - y1
        char_positions.append((ch, x1, y1_pil, x2, y2_pil))

    # Loop through OCR lines
    n_boxes = len(data['level'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if text and float(data['conf'][i]) > 10:
            dob_result = detect_pii_dob(text)
            if dob_result['contains_pii_dob']:
                print(f"PII DOB Detected in Line: {text}")

                # Bounding box of this line
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

                # Take first DOB match (if multiple)
                dob_details = dob_result['dob_details'][0]
                dob_day = str(dob_details.get("day", "")).zfill(2)
                dob_month = str(dob_details.get("month", "")).zfill(2)
                print(f"Details: {dob_details} Date: {dob_day} Month: {dob_month}")

               # Store redacted chars for debug
                redacted_value = ""
                redacted_count = 0

                # Redact only day + month chars
                for ch, cx1, cy1, cx2, cy2 in char_positions:
                    if (cx1 >= x and cx2 <= x + w) and (cy1 >= y and cy2 <= y + h):
                        if redacted_count < 5:
                            draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
                            redacted_value += ch   # collect the char
                            redacted_count += 1

                if redacted_value:
                    print(f"Redacted DOB part: {redacted_value} , {redacted_count}")

    # Save & return
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()