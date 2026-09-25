from api.utils.regex import pan_pattern

def detect_pan_card_no(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

   # PAN
    for match in pan_pattern.findall(text):
        matches.append("PAN")
        pii_values.append({"type": "PAN", "value": match})

    return {
        "matches": matches,
        "contains_pan_card_no": bool(matches),
        "pan_card_no_details": pii_values
    }