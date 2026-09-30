"""
Detection rules for PrivyLens.

Each rule is a regex plus (optionally) a validator that cuts down false
positives (Luhn for cards, Verhoeff for Aadhaar). If a rule has a capture
group named "v", only that group is flagged, so "password: hunter2" flags
"hunter2" and leaves the label alone.
"""
import re
from dataclasses import dataclass
from typing import Callable, Optional

RISK_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


# ---------- validators ----------

def luhn_ok(s: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", s)]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


_D = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],
      [3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
      [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],
      [9,8,7,6,5,4,3,2,1,0]]
_P = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],
      [8,9,1,6,0,4,3,5,2,7],[9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],
      [2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]


def verhoeff_ok(s: str) -> bool:
    digits = re.sub(r"\D", "", s)
    if len(digits) != 12 or digits[0] in "01":  # Aadhaar never starts with 0/1
        return False
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def _not_placeholder(s: str) -> bool:
    """Skip obvious dummy values like 'password', '********', 'changeme'."""
    low = s.lower()
    return not (set(low) <= set("*x•.-_") or low in {"password", "changeme", "example", "secret", "null", "none", "true", "false"})


# ---------- rule table ----------

@dataclass
class Rule:
    type: str
    label: str
    risk: str
    regex: re.Pattern
    validator: Optional[Callable[[str], bool]] = None


def _r(type_, label, risk, pattern, validator=None, flags=0):
    return Rule(type_, label, risk, re.compile(pattern, flags), validator)


SENSITIVE_PARAMS = r"(?:access_token|id_token|refresh_token|token|api[_-]?key|apikey|key|secret|sig|signature|password|passwd|pwd|auth|session(?:id)?|sid|code)"

RULES = [
    # --- secrets & credentials ---
    _r("PRIVATE_KEY", "Private key block", "critical",
       r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)"),
    _r("AWS_KEY", "AWS access key", "critical", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    _r("GITHUB_TOKEN", "GitHub token", "critical", r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    _r("GOOGLE_KEY", "Google API key", "critical", r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    _r("SLACK_TOKEN", "Slack token", "critical", r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    _r("STRIPE_KEY", "Stripe key", "critical", r"\b[sr]k_live_[A-Za-z0-9]{16,}\b"),
    _r("API_KEY", "API key (sk-…)", "critical", r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}\b"),
    _r("JWT", "JSON web token", "high", r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    _r("PASSWORD", "Password / secret value", "critical",
       r"(?i)(?<![?&])\b(?:password|passwd|pwd|passcode|pass|secret(?:[_ -]?key)?|api[_ -]?key|access[_ -]?token|auth[_ -]?token|client[_ -]?secret)\b\s*(?:is\s*)?[:=]\s*[\"']?(?P<v>[^\s\"',;&]{4,})",
       _not_placeholder),
    _r("SENSITIVE_URL", "URL with a token in it", "high",
       rf"(?i)https?://[^\s\"'<>]*?[?&]{SENSITIVE_PARAMS}=(?P<v>[^&\s\"'<>#]{{4,}})"),

    # --- financial / government ids ---
    _r("CARD", "Credit / debit card number", "critical",
       r"(?<![\d-])\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{1,7}(?![\d-])", luhn_ok),
    _r("AADHAAR", "Aadhaar number", "high", r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)", verhoeff_ok),
    _r("PAN", "PAN card number", "high", r"\b[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]\b"),
    _r("SSN", "US Social Security number", "high",
       r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"),
    _r("IFSC", "IFSC code", "low", r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),

    # --- contact & personal ---
    _r("EMAIL", "Email address", "medium", r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}\b"),
    _r("PHONE", "Phone number", "medium",
       r"(?<![\d.])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)"),
    _r("PHONE_INTL", "Phone number (intl.)", "medium",
       r"(?<![\w.])\+(?!91)\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}(?!\d)"),
    _r("DOB", "Date of birth", "medium",
       r"(?i)\b(?:dob|d\.o\.b|date of birth|born(?: on)?)\b\s*[:\-]?\s*(?P<v>\d{1,2}[/\-. ]\d{1,2}[/\-. ]\d{2,4}|\d{4}-\d{2}-\d{2})"),
    _r("PINCODE", "Address / PIN code", "low",
       r"(?i)\b(?:pin(?:\s?code)?|zip(?:\s?code)?)\b\s*[:\-]?\s*(?P<v>\d{5,6})\b"),
]
