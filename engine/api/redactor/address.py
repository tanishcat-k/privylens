from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from api.detector.address import detect_pii_address
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np
import cv2
import re



# ---- Image Redactor (Only Address) ----
def redact_address_from_image(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # OCR with word-level positions
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--oem 1"
    )

    # Group into lines
    lines = {}
    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        if word and float(data['conf'][i]) > 10:
            key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            if key not in lines:
                lines[key] = {"text": [], "positions": []}
            lines[key]["text"].append(word)
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            lines[key]["positions"].append((x, y, w, h))

    # 🔹 Detect and redact addresses
    for line in lines.values():
        line_text = " ".join(line["text"])
        result = detect_pii_address(line_text)

        if result['contains_pii_address']:
            print(f"[ADDRESS REDACTED] {line_text}")
            for (x, y, w, h) in line["positions"]:
                draw.rectangle([x, y, x + w, y + h], fill="black")

    # Return processed image
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()