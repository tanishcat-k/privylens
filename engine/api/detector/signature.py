from api.utils.keyword import SIGNATURE_KEYWORDS

def detect_signature_keywords(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    for kw in SIGNATURE_KEYWORDS:
        if kw in lower_text:
            matches.append("SIGNATURE_KEYWORD")
            pii_values.append({"type": "SIGNATURE", "value": kw})

    return {
        "matches": matches,
        "contains_signature_keyword": bool(matches),
        "pii_details": pii_values
    }
    