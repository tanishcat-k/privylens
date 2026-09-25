import re
from api.utils.regex import mobile_pattern

def detect_mobile_number(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    # Find all mobile numbers
    for match in mobile_pattern.findall(text):
        digits = re.sub(r'\D', '', match)  # remove spaces/dashes
        if len(digits) == 10 or (len(digits) == 12 and digits.startswith("91")):
            matches.append("MOBILE")
            pii_values.append({"type": "MOBILE", "value": match})

    return {
        "matches": matches,
        "contains_mobile_number": bool(matches),
        "mobile_number_details": pii_values
    }
