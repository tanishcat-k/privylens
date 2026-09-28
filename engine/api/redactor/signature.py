from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from api.detector.signature import detect_signature_keywords
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np
import cv2
import re


def redact_signatures_from_image(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    np_img = np.array(image)

    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    draw = ImageDraw.Draw(image)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        # basic size heuristic
        if not (50 < w < 600 and 20 < h < 200 and w > h):
            continue

        sig_crop = image.crop((x, y, x + w, y + h))
        text_in_region = pytesseract.image_to_string(sig_crop).strip()

        # ✅ Use your signature keyword detector
        keyword_check = detect_signature_keywords(text_in_region)

        # Skip if text is clean normal text without signature keywords
        if text_in_region and not keyword_check["contains_signature_keyword"]:
            continue

        # Otherwise redact
        print(f"[SIGNATURE REDACTED] at (x={x}, y={y}, w={w}, h={h}) | OCR guess: '{text_in_region}'")
        draw.rectangle([x, y, x + w, y + h], fill="black")

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# def redact_signatures_from_image(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     np_img = np.array(image)

#     gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
#     _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

#     kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
#     morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

#     contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     draw = ImageDraw.Draw(image)

#     for cnt in contours:
#         x, y, w, h = cv2.boundingRect(cnt)
#         # signature heuristic: wider than tall, not too small, not huge
#         if 50 < w < 600 and 20 < h < 200 and w > h:
#             # Extract possible signature region for logging
#             sig_crop = image.crop((x, y, x + w, y + h))

#             # Run OCR inside the suspected signature region
#             text_in_region = pytesseract.image_to_string(sig_crop).strip()

#             # Print log in console
#             print(f"[SIGNATURE REDACTED] at (x={x}, y={y}, w={w}, h={h}) | OCR guess: '{text_in_region}'")
#             draw.rectangle([x, y, x+w, y+h], fill="black")


#     buf = io.BytesIO()
#     image.save(buf, format="PNG")
#     buf.seek(0)
#     return buf.read()