from api.utils.regex import dl_pattern

def detect_driving_licence_no(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    # DL
    for match in dl_pattern.findall(text):
        matches.append("DRIVING_LICENSE")
        pii_values.append({"type": "DRIVING_LICENSE", "value": match})

    return {
        "matches": matches,
        "contains_driving_licence_no": bool(matches),
        "driving_licence_no_details": pii_values
    }
