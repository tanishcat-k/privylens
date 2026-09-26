import re
from datetime import datetime
from api.utils.regex import dob_pattern, short_date_pattern

def is_valid_date(date_str):
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d %m %Y", "%Y-%m-%d", "%Y/%m/%d", "%Y %m %d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if dt <= today:
                return True
            else:
                return False
        except ValueError:
            continue
    return False


def detect_pii_dob(text: str) -> dict:
    matches = []
    pii_values = []
    lower_text = text.lower()
    
    # Full DOB formats
    for match in dob_pattern.findall(text):
        cleaned = re.sub(r'[-/\s]', '-', match)
        if is_valid_date(cleaned):
            try:
                # Try parsing date
                dt = None
                for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d %m %Y", "%Y-%m-%d", "%Y/%m/%d", "%Y %m %d"):
                    try:
                        dt = datetime.strptime(cleaned, fmt)
                        break
                    except ValueError:
                        continue

                if dt:
                    matches.append("DOB")
                    pii_values.append({
                        "type": "DOB",
                        "value": match,
                        "day": dt.day,
                        "month": dt.month,
                        "year": dt.year
                    })
            except ValueError:
                continue

    # Compact DOB format (ddmmyyyy)
    compact_dob = re.findall(r'\b\d{8}\b', text)
    for dob in compact_dob:
        try:
            dt = datetime.strptime(dob, "%d%m%Y")
            matches.append("DOB")
            pii_values.append({
                "type": "DOB",
                "value": dob,
                "day": dt.day,
                "month": dt.month,
                "year": dt.year
            })
        except ValueError:
            continue
        
    # Short date detection (MM/YY or MM/DD) → treat only as month+day
    for match in short_date_pattern.findall(text):
        month_str, part2_str = match
        month = int(month_str)
        part2 = int(part2_str)
        if 1 <= month <= 12 and part2 <= 31:
            matches.append("SHORT_DATE")
            pii_values.append({
                "type": "SHORT_DATE",
                "value": f"{month:02d}/{part2:02d}",
                "day": part2,
                "month": month,
                "year": None
            })
        
    return {
        "matches": matches,
        "contains_pii_dob": bool(matches),
        "dob_details": pii_values
    }
    
    
# def detect_pii_dob(text: str) -> dict:
#     matches = []
#     pii_values = []
#     lower_text = text.lower()
    
#     # DOB with validation
#     for match in dob_pattern.findall(text):
#         cleaned = re.sub(r'[-/\s]', '-', match)
#         if is_valid_date(cleaned):
#             matches.append("DOB")
#             pii_values.append({"type": "DOB", "value": match})


#     # Compact DOB format (ddmmyyyy)
#     compact_dob = re.findall(r'\b\d{8}\b', text)
#     for dob in compact_dob:
#         try:
#             datetime.strptime(dob, "%d%m%Y")
#             matches.append("DOB")
#             pii_values.append({"type": "DOB", "value": dob})
#         except ValueError:
#             continue
        
#     # Short date detection (MM/YY or MM/DD)
#     for match in short_date_pattern.findall(text):
#         month_str, part2_str = match
#         month = int(month_str)
#         part2 = int(part2_str)
#         if 1 <= month <= 12:
#             # Part2 can be day (<=31) or year (any 2-digit usually)
#             if part2 <= 31:
#                 matches.append("SHORT_DATE")
#                 pii_values.append({"type": "SHORT_DATE", "value": f"{month:02d}/{part2:02d}"})
        
#     return {
#         "matches": matches,
#         "contains_pii_dob": bool(matches),
#         "pii_details": pii_values
#     }