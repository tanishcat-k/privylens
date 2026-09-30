"""Core detection engine: text in, list of findings out."""
from .patterns import RULES, RISK_ORDER


def mask_preview(value: str, rtype: str) -> str:
    """What we show in the UI list. Secrets get almost fully hidden."""
    v = value.strip()
    if len(v) <= 4:
        return "•" * len(v)
    if rtype in {"PASSWORD", "PRIVATE_KEY", "API_KEY", "AWS_KEY", "GITHUB_TOKEN", "GOOGLE_KEY",
                 "SLACK_TOKEN", "STRIPE_KEY", "JWT", "SENSITIVE_URL"}:
        return v[:2] + "•" * 6
    return v[:2] + "•" * min(len(v) - 4, 10) + v[-2:]


def find_pii(text: str):
    """Return non-overlapping findings sorted by position."""
    raw = []
    for rule in RULES:
        for m in rule.regex.finditer(text):
            has_v = "v" in rule.regex.groupindex and m.group("v") is not None
            s, e = (m.start("v"), m.end("v")) if has_v else (m.start(), m.end())
            value = text[s:e]
            if rule.validator and not rule.validator(value):
                continue
            raw.append({"type": rule.type, "label": rule.label, "risk": rule.risk,
                        "start": s, "end": e, "value": value})

    # Overlaps: keep the riskier match, then the longer one.
    raw.sort(key=lambda f: (-RISK_ORDER[f["risk"]], -(f["end"] - f["start"]), f["start"]))
    kept = []
    for f in raw:
        if all(f["end"] <= k["start"] or f["start"] >= k["end"] for k in kept):
            kept.append(f)
    kept.sort(key=lambda f: f["start"])
    for f in kept:
        f["preview"] = mask_preview(f["value"], f["type"])
    return kept


def summarize(findings):
    by_risk = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        by_risk[f["risk"]] += 1
    if by_risk["critical"]:
        verdict = "Do not share this yet"
    elif by_risk["high"]:
        verdict = "Redact before sharing"
    elif by_risk["medium"] or by_risk["low"]:
        verdict = "Worth a quick review"
    else:
        verdict = "Nothing sensitive found"
    return {"total": len(findings), "by_risk": by_risk, "verdict": verdict}


def apply_text_redaction(text: str, findings, replacement="[REDACTED]") -> str:
    out, last = [], 0
    for f in sorted(findings, key=lambda f: f["start"]):
        out.append(text[last:f["start"]])
        out.append(replacement)
        last = f["end"]
    out.append(text[last:])
    return "".join(out)
