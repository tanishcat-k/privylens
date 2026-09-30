"""Turn uploaded files into text + positions, and apply redactions back."""
import base64
import io
import re

import pytesseract
from docx import Document
from pdf2image import convert_from_bytes
from PIL import Image, ImageDraw

from .engine import apply_text_redaction, find_pii, summarize

PDF_DPI = 150
PREVIEW_MAX_W = 1200
PAD = 3  # px of breathing room around black boxes


def kind_of(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext in {"png", "jpg", "jpeg", "webp"}:
        return "image"
    if ext == "pdf":
        return "pdf"
    if ext == "docx":
        return "docx"
    raise ValueError("Unsupported file type. Use PNG, JPG, PDF or DOCX.")


# ---------------- images ----------------

def _ocr_page(img: Image.Image):
    """Return (text, words). Each word knows its char span in `text` and its pixel box."""
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    text, words, last_line = "", [], None
    for i, raw in enumerate(data["text"]):
        w = raw.strip()
        if not w or float(data["conf"][i]) < 0:
            continue
        line = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        if last_line is not None:
            text += " " if line == last_line else "\n"
        start = len(text)
        text += w
        words.append({"start": start, "end": len(text), "line": line,
                      "box": (data["left"][i], data["top"][i], data["width"][i], data["height"][i])})
        last_line = line
    return text, words


def _boxes_for(finding, words):
    """Union the word boxes of a finding, one box per text line."""
    per_line = {}
    for w in words:
        if w["end"] > finding["start"] and w["start"] < finding["end"]:
            x, y, bw, bh = w["box"]
            x0, y0, x1, y1 = per_line.get(w["line"], (x, y, x + bw, y + bh))
            per_line[w["line"]] = (min(x0, x), min(y0, y), max(x1, x + bw), max(y1, y + bh))
    return [(x0, y0, x1 - x0, y1 - y0) for x0, y0, x1, y1 in per_line.values()]


def _scan_pages(images):
    pages, findings = [], []
    for p, img in enumerate(images):
        img = img.convert("RGB")
        text, words = _ocr_page(img)
        W, H = img.size
        for i, f in enumerate(find_pii(text)):
            boxes = _boxes_for(f, words)
            if not boxes:
                continue
            f.update(id=f"p{p}-{i}", page=p,
                     boxes=[[x / W, y / H, w / W, h / H] for x, y, w, h in boxes],
                     _px=boxes)
            findings.append(f)
        prev = img.copy()
        if W > PREVIEW_MAX_W:
            prev = prev.resize((PREVIEW_MAX_W, int(H * PREVIEW_MAX_W / W)))
        buf = io.BytesIO()
        prev.save(buf, format="JPEG", quality=82)
        pages.append({"image": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(),
                      "width": W, "height": H})
    return pages, findings


def _load_images(kind, data):
    if kind == "pdf":
        return convert_from_bytes(data, dpi=PDF_DPI)
    return [Image.open(io.BytesIO(data))]


# ---------------- docx ----------------

def _iter_paragraphs(doc):
    def walk(container):
        for p in container.paragraphs:
            yield p
        for t in getattr(container, "tables", []):
            for row in t.rows:
                for cell in row.cells:
                    yield from walk(cell)
    yield from walk(doc)
    for s in doc.sections:
        for part in (s.header, s.footer):
            yield from walk(part)


def _docx_blocks(data):
    doc = Document(io.BytesIO(data))
    blocks, findings, seen = [], [], set()
    for p in _iter_paragraphs(doc):
        if id(p._p) in seen or not p.text.strip():
            continue
        seen.add(id(p._p))
        bid = f"b{len(blocks)}"
        blocks.append({"id": bid, "text": p.text})
        for i, f in enumerate(find_pii(p.text)):
            f.update(id=f"{bid}-{i}", block=bid)
            findings.append(f)
    return doc, blocks, findings


def _redact_paragraph(p, findings, replacement):
    """Replace spans while keeping the run formatting intact."""
    runs = p.runs
    offsets, pos = [], 0
    for r in runs:
        offsets.append((pos, pos + len(r.text)))
        pos += len(r.text)
    for f in sorted(findings, key=lambda f: -f["start"]):
        first = True
        for r, (a, b) in zip(runs, offsets):
            if b <= f["start"] or a >= f["end"]:
                continue
            s, e = max(f["start"], a) - a, min(f["end"], b) - a
            r.text = r.text[:s] + (replacement if first else "") + r.text[e:]
            first = False


# ---------------- public API ----------------

def scan_file(filename: str, data: bytes) -> dict:
    kind = kind_of(filename)
    if kind == "docx":
        _, blocks, findings = _docx_blocks(data)
        return {"kind": kind, "filename": filename, "blocks": blocks,
                "findings": findings, "summary": summarize(findings)}
    pages, findings = _scan_pages(_load_images(kind, data))
    for f in findings:
        f.pop("_px", None)
    return {"kind": kind, "filename": filename, "pages": pages,
            "findings": findings, "summary": summarize(findings)}


def scan_text(text: str) -> dict:
    findings = find_pii(text)
    for i, f in enumerate(findings):
        f.update(id=f"t-{i}", block="t0")
    return {"kind": "text", "filename": "pasted text", "blocks": [{"id": "t0", "text": text}],
            "findings": findings, "summary": summarize(findings)}


def redact_file(filename: str, data: bytes, exclude=()):
    """Returns (bytes, media_type, extension). `exclude` = finding ids the user chose to keep."""
    kind, exclude = kind_of(filename), set(exclude)
    if kind == "docx":
        doc, blocks, findings = _docx_blocks(data)
        by_block = {}
        for f in findings:
            if f["id"] not in exclude:
                by_block.setdefault(f["block"], []).append(f)
        seen, idx = set(), 0
        for p in _iter_paragraphs(doc):
            if id(p._p) in seen or not p.text.strip():
                continue
            seen.add(id(p._p))
            _redact_paragraph(p, by_block.get(f"b{idx}", []), "[REDACTED]")
            idx += 1
        out = io.BytesIO()
        doc.save(out)
        return (out.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx")

    images = _load_images(kind, data)
    _, findings = _scan_pages(images)
    done = []
    for p, img in enumerate(images):
        img = img.convert("RGB")
        d = ImageDraw.Draw(img)
        for f in findings:
            if f["page"] == p and f["id"] not in exclude:
                for x, y, w, h in f["_px"]:
                    d.rectangle([x - PAD, y - PAD, x + w + PAD, y + h + PAD], fill="black")
        done.append(img)
    out = io.BytesIO()
    if kind == "pdf":  # rasterised on purpose: no hidden text layer left underneath the boxes
        done[0].save(out, format="PDF", save_all=True, append_images=done[1:], resolution=PDF_DPI)
        return out.getvalue(), "application/pdf", "pdf"
    done[0].save(out, format="PNG")
    return out.getvalue(), "image/png", "png"
