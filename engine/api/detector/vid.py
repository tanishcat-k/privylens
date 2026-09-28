from api.utils.regex import vid_pattern

def detect_vid(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()

    # VID
    for match in vid_pattern.findall(text):
        matches.append("VID")
        pii_values.append({"type": "VID", "value": match})
        
    return {
        "matches": matches,
        "contains_vid": bool(matches),
        "vid_details": pii_values
    }