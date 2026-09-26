from api.utils.regex import email_pattern

def detect_email(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    # Email
    for match in email_pattern.findall(text):
        matches.append("EMAIL")
        pii_values.append({"type": "EMAIL", "value": match})

    return {
        "matches": matches,
        "contains_email": bool(matches),
        "email_details": pii_values
    }