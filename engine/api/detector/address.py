import re
from api.utils.keyword import ADDRESS_KEYWORDS

def detect_pii_address(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()
    
    # Address
    if any(kw in lower_text for kw in ADDRESS_KEYWORDS):
        matches.append("ADDRESS")
        pii_values.append({"type": "ADDRESS", "value": "Found by keyword"})
        
    # Pincode
    pin_match = re.search(r"\b[1-9][0-9]{5}\b", text)
    if pin_match:
        matches.append("ADDRESS_PINCODE")
        pii_values.append({"type": "ADDRESS", "value": f"PIN Code: {pin_match.group()}"})
        
    return {
        "matches": matches,
        "contains_pii_address": bool(matches),
        "address_details": pii_values
    }