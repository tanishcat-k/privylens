import re
import io
from docx import Document
from api.detector.aadhar_card_no import detect_aadhar_card_no
from api.detector.mobile_number import detect_mobile_number
from api.detector.dob import detect_pii_dob
from api.detector.driving_licence_no import detect_driving_licence_no
from api.detector.address import detect_pii_address
from api.detector.vid import detect_vid

# ------------------ Masking Functions ------------------ #

def mask_aadhaar(aadhaar: str) -> str:
    digits = re.sub(r"\D", "", aadhaar)
    if len(digits) == 12:
        return digits[:2] + "XXXX XXXX " + digits[-2:]
    return "[REDACTED]"

def mask_mobile(mobile: str) -> str:
    digits = re.sub(r"\D", "", mobile)
    if len(digits) == 10:
        return digits[:2] + "XXXXXX" + digits[-2:]
    elif len(digits) == 12 and digits.startswith("91"):
        return "+91 " + digits[2:4] + "XXXXXX" + digits[-2:]
    return "[REDACTED]"

def mask_pan(pan: str) -> str:
    pan = pan.strip()
    if len(pan) == 10:
        return pan[:2] + "XXXXXX" + pan[-2:]
    return "[REDACTED]"

def mask_dl(dl: str) -> str:
    dl = dl.strip()
    if len(dl) >= 6:  # assume valid DL number has >= 6 chars
        return dl[:2] + "XX XXXXXXXXX" + dl[-2:]
    return "[REDACTED]"

def mask_vid(vid: str) -> str:
    digits = re.sub(r"\D", "", vid)
    if len(digits) == 16:
        return digits[:2] + "XX XXXX XXXX XX " + digits[-2:]
    return "[REDACTED]"

def mask_dob(dob: str) -> str:
    dob = dob.strip()
    match = re.search(r"(\d{2})[/-](\d{2})[/-](\d{4})", dob)
    if match:
        return "XX/XX/" + match.group(3)
    match = re.search(r"(\d{4})[/-](\d{2})[/-](\d{2})", dob)
    if match:
        return "XX/XX/" + match.group(1)
    return "[REDACTED]"

def mask_address(address: str) -> str:
    return "[REDACTED]"


# ------------------ DOCX Redaction ------------------ #

def redact_docx_with_pii(docx_bytes: bytes) -> bytes:
    doc = Document(io.BytesIO(docx_bytes))

    for para in doc.paragraphs:
        for run in para.runs:
            text = run.text

            # Aadhaar
            aadhaar_info = detect_aadhar_card_no(text)
            for item in aadhaar_info.get("aadhar_card_no_details", []):
                text = text.replace(item["value"], mask_aadhaar(item["value"]))

            # Mobile
            mobile_info = detect_mobile_number(text)
            for item in mobile_info.get("mobile_number_details", []):
                text = text.replace(item["value"], mask_mobile(item["value"]))

            # Driving Licence
            dl_info = detect_driving_licence_no(text)
            for item in dl_info.get("driving_licence_no_details", []):
                text = text.replace(item["value"], mask_dl(item["value"]))

            # PAN
            text = re.sub(r'([A-Z]{5}[0-9]{4}[A-Z])',
                          lambda m: mask_pan(m.group()), text)

            # DOB
            dob_info = detect_pii_dob(text)
            for item in dob_info.get("dob_details", []):
                text = text.replace(item["value"], mask_dob(item["value"]))

            # Address
            addr_info = detect_pii_address(text)
            for item in addr_info.get("address_details", []):
                text = text.replace(item["value"], mask_address(item["value"]))

            # VID
            vid_info = detect_vid(text)
            for item in vid_info.get("vid_details", []):
                text = text.replace(item["value"], mask_vid(item["value"]))

            run.text = text  # update run text (preserves style)

    out_buf = io.BytesIO()
    doc.save(out_buf)
    out_buf.seek(0)
    return out_buf.read()
