import io
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.privylens.files import redact_file, scan_file, scan_text

load_dotenv()

# Only needed on Windows installs where Tesseract can't find its language data.
if os.name == "nt" and not os.getenv("TESSDATA_PREFIX"):
    os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

app = FastAPI(title="PrivyLens API")

origins = [o.strip() for o in os.getenv("FRONTEND_URL", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

MAX_BYTES = 15 * 1024 * 1024


class TextIn(BaseModel):
    text: str


async def _read(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File is over 15 MB.")
    return data


@app.get("/")
async def root():
    return {"message": "PrivyLens backend is running."}


@app.post("/api/scan")
async def api_scan(file: UploadFile = File(...)):
    try:
        return scan_file(file.filename, await _read(file))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/scan-text")
async def api_scan_text(body: TextIn):
    return scan_text(body.text[:200_000])


@app.post("/api/redact")
async def api_redact(file: UploadFile = File(...), exclude: str = Form("[]")):
    try:
        out, media, ext = redact_file(file.filename, await _read(file), json.loads(exclude))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return StreamingResponse(io.BytesIO(out), media_type=media,
                             headers={"Content-Disposition": f'attachment; filename="redacted.{ext}"'})
