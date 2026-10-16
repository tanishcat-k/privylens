# PrivyLens

Find sensitive info in a screenshot, PDF, Word file or pasted text before you share it, and download a copy with it blacked out.

Built on [PII-Detector](https://github.com/PII-Detector/Pii-detector). Its OCR, PDF and DOCX handling are kept as the detection engine; the app around it is MERN.

```
React (client)  ->  Express (server)  ->  Python engine (OCR + rules)
                        |
                     MongoDB  (scan history: file name + masked samples only)
```

| Folder   | What it is |
|----------|------------|
| `client/` | React + Vite UI. Findings show up as bars on the document; click one to keep or redact it. |
| `server/` | Express API. Validates uploads, calls the engine, saves history to MongoDB. |
| `engine/` | The base repo's FastAPI service, extended: new rule set in `api/privylens/`, tests in `tests/`. |

## Run it

You need Node 22, Python 3.12+, Tesseract and Poppler (`sudo apt install tesseract-ocr poppler-utils` / `brew install tesseract poppler`), and MongoDB (local or Atlas; the app still scans without it, only History turns off).

```bash
# 1. engine
cd engine
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn api.index:app --port 8000

# 2. server + client (new terminal, from the repo root)
cp server/.env.example server/.env
npm install && npm run install:all
npm run dev
```

Open http://localhost:5173. Engine tests: `cd engine && pytest`.

## What it detects

Emails, Indian and international phone numbers, Aadhaar (Verhoeff checked), PAN, US SSN, card numbers (Luhn checked), IFSC, DOB, PIN codes, passwords and `key = value` secrets, AWS / GitHub / Google / Slack / Stripe / `sk-` keys, JWTs, private key blocks, and URLs carrying tokens. Each gets a risk level (critical to low); the verdict at the top is driven by the worst one.

Rules live in `engine/api/privylens/patterns.py`, one line each. Adding a type is adding a line.

## Notes for the team

- Uploaded files are held in memory only. Mongo gets the file name, risk counts and masked samples like `ta••••••om`, never the raw values.
- Redacted PDFs are rasterised on purpose, so there's no hidden text layer under the boxes.
- Detection is rules-based and will miss things (names and free-text addresses, mainly). Ideas for next: NER for names, user accounts so history is per person, a "paste a URL" mode.
