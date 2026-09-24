from PIL import Image, ImageDraw, ImageEnhance
from pdf2image import convert_from_bytes
from docx import Document
# from PyPDF2 import PdfReader
import pytesseract
import io
# from fpdf import FPDF
from api.detector.aadhar_card_no import detect_aadhar_card_no
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import numpy as np
import cv2
import re




# ----------------------------------------------- #
# Aadhar card no redactor based on character - with 8 digits complete working

def redact_image_with_aadhar_card_no(image_bytes: bytes) -> bytes:
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
        result = detect_aadhar_card_no(line_text)

        if result['contains_aadhar_card_no']:
            print(f"Aadhar Card No Detected in Line: {line_text}")

            # Find bounding box for this line
            min_x = min(p[0] for p in line["positions"])
            min_y = min(p[1] for p in line["positions"])
            max_x = max(p[0] + p[2] for p in line["positions"])
            max_y = max(p[1] + p[3] for p in line["positions"])

            for pii in result['aadhar_card_no_details']:
                aadhar_value = re.sub(r'\D', '', pii['value'])  # only digits
                total_len = len(aadhar_value)
                redact_start = 2
                redact_end = total_len - 2
                target_index = 0
                # max_redact = 8  # redact first 8 digits (change if needed)

                for ch, cx1, cy1, cx2, cy2 in char_positions:
                    if (
                        # target_index < max_redact
                        target_index < total_len
                        and ch.isdigit()
                        and cx1 >= min_x and cx2 <= max_x and cy1 >= min_y and cy2 <= max_y
                        and ch == aadhar_value[target_index]
                    ):  # redact only for last digits
                        # draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
                        # target_index += 1
                        
                        # redact only middle digits
                        if redact_start <= target_index < redact_end:
                            draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
                        target_index += 1
                        
                        

    # Save image to bytes
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output.read()


# ------------------------------------ # 
# aadhar card no redactor based on character 

# def redact_image_with_aadhar_card_no(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))
#     draw = ImageDraw.Draw(image)
#     width, height = image.size

#     # OCR line-level data
#     data = pytesseract.image_to_data(
#         image,
#         output_type=pytesseract.Output.DICT,
#         config="--oem 1"
#     )

#     # OCR character boxes
#     char_boxes = pytesseract.image_to_boxes(image, config="--oem 3")
#     char_positions = []
#     for box in char_boxes.splitlines():
#         ch, x1, y1, x2, y2, _ = box.split()
#         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#         y1_pil = height - y2
#         y2_pil = height - y1
#         char_positions.append((ch, x1, y1_pil, x2, y2_pil))

#     # Group OCR results by line
#     lines = {}
#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if word and float(data['conf'][i]) > 10:
#             key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
#             if key not in lines:
#                 lines[key] = {"text": [], "positions": [], "raw_words": []}
#             lines[key]["text"].append(word)
#             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#             lines[key]["positions"].append((x, y, w, h))
#             lines[key]["raw_words"].append((word, x, y, w, h))

#     # Redact Aadhaar digits character-wise
#     for line in lines.values():
#         line_text = " ".join(line["text"])
#         result = detect_aadhar_card_no(line_text)
#         if result['contains_aadhar_card_no']:
#             print(f"Aadhar Card No Detected in Line: {line_text}")

#             for pii in result['aadhar_card_no_details']:
#                 aadhar_value = re.sub(r'\D', '', pii['value'])  # only digits
#                 redacted_value = ""
#                 target_index = 0
#                 # max_redact = len(aadhar_value)  # change to 8 if you want only first 8 digits
#                 max_redact = 8

#                 # Iterate over all character boxes
#                 for ch, cx1, cy1, cx2, cy2 in char_positions:
#                     if target_index < max_redact and ch == aadhar_value[target_index]:
#                         draw.rectangle([cx1, cy1, cx2, cy2], fill="black")
#                         redacted_value += ch
#                         target_index += 1

#                 print(f"Redacted Aadhaar digits: {redacted_value}")

#     # Save image to bytes
#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()



# ------------------------------------------ #
# For Aadhar Card
# def redact_image_with_aadhar_card_no(image_bytes: bytes) -> bytes:
#     image = Image.open(io.BytesIO(image_bytes))
#     draw = ImageDraw.Draw(image)
#     width, height = image.size

#     # ---- Step 2: OCR line-level + word-level data ----
#     data = pytesseract.image_to_data(
#         image, 
#         output_type=pytesseract.Output.DICT, 
#         config="--oem 1"
#     )

#     char_boxes = pytesseract.image_to_boxes(image, config="--oem 1")
#     char_positions = []
#     for box in char_boxes.splitlines():
#         ch, x1, y1, x2, y2, _ = box.split()
#         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#         y1_pil = height - y2
#         y2_pil = height - y1
#         char_positions.append((ch, x1, y1_pil, x2, y2_pil))

#     lines = {}
#     for i in range(len(data['text'])):
#         word = data['text'][i].strip()
#         if word and float(data['conf'][i]) > 10:
#             key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
#             if key not in lines:
#                 lines[key] = {"text": [], "positions": [], "raw_words": []}
#             lines[key]["text"].append(word)
#             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#             lines[key]["positions"].append((x, y, w, h))
#             lines[key]["raw_words"].append((word, x, y, w, h))


#     for line in lines.values():
#         line_text = " ".join(line["text"])
     
#         result = detect_aadhar_card_no(line_text)
#         if result['contains_aadhar_card_no']:
#             print(f"Aadhar Card No Detected in Line: {line_text}")
#             for (x, y, w, h) in line["positions"]:
#                 draw.rectangle([x, y, x + w, y + h], fill="black")

#     output = io.BytesIO()
#     image.save(output, format='PNG')
#     output.seek(0)
#     return output.read()
