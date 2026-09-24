import re
from api.utils.verhoeff_algorithm import validate_verhoeff
from api.utils.regex import aadhaar_pattern

def detect_aadhar_card_no(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    # Aadhaar detection with Verhoeff check
    for match in aadhaar_pattern.findall(text):
        digits = re.sub(r'\D', '', match)
        if len(digits) == 12 and validate_verhoeff(digits):
            matches.append("AADHAAR")
            pii_values.append({"type": "AADHAAR", "value": match})

    return {
        "matches": matches,
        "contains_aadhar_card_no": bool(matches),
        "aadhar_card_no_details": pii_values
    }