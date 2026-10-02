import re

# Regex Patterns for PII

aadhaar_pattern = re.compile(r'\b(?:\d[ -]?){4}(?:\d[ -]?){4}(?:\d[ -]?){4}\b')
pan_pattern = re.compile(r'\b[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]\b')
email_pattern = re.compile(r'\b\S+@\S+\.\S+\b')
mobile_pattern = re.compile(r'(?:\+91[\-\s]?|91[\-\s]?)?[6-9]\d{9}')
vid_pattern = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
dl_pattern = re.compile(r'\b[A-Z]{2}[ -]?\d{2}[ -]?\d{4}[ -]?\d{7}\b')
dob_pattern = re.compile(r'\b(?:\d{2}[-/\s]?\d{2}[-/\s]?\d{4}|\d{4}[-/\s]?\d{2}[-/\s]?\d{2})\b')
short_date_pattern = re.compile(r'\b(0[1-9]|1[0-2])[/\-](\d{2})\b')