from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from api.detector.pan_card_no import detect_pan_card_no
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np
import cv2
import re

# -------------------------- #
# Pan card no - character based
def redact_image_with_pan_card_no(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # OCR line-level data
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--oem 1"
    )

    # Group OCR results by line
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

    # Now get character boxes once
    char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
    char_positions = []
    for box in char_boxes.splitlines():
        ch, x1, y1, x2, y2, _ = box.split()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        y1_pil = height - y2
        y2_pil = height - y1
        char_positions.append((ch, x1, y1_pil, x2, y2_pil))

    # Process each line
    for line in lines.values():
        line_text = " ".join(line["text"])
        result = detect_pan_card_no(line_text)

        if result['contains_pan_card_no']:
            print(f"Driving Licence No Detected in Line: {line_text}")

            # Find bounding box for this line
            min_x = min(p[0] for p in line["positions"])
            min_y = min(p[1] for p in line["positions"])
            max_x = max(p[0] + p[2] for p in line["positions"])
            max_y = max(p[1] + p[3] for p in line["positions"])
            
            for pii in result['pan_card_no_details']:
                pan_no_value = re.sub(r'\W', '', pii['value'])  # keep alphanumeric only
                total_len = len(pan_no_value)

                # Characters to redact: from index 2 to total_len-3
                redact_start = 2
                redact_end = total_len - 2  

                target_index = 0
                for ch, cx1, cy1, cx2, cy2 in char_positions:
                    if (
                        target_index < total_len
                        and cx1 >= min_x and cx2 <= max_x and cy1 >= min_y and cy2 <= max_y
                        and ch.upper() == pan_no_value[target_index].upper()
                    ):
                        # redact only middle characters
                        if redact_start <= target_index < redact_end:
                            draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
                        target_index += 1

    # Save image to bytes
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()