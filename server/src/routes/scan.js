import { Router } from "express";
import multer from "multer";
import Scan from "../models/Scan.js";
import { db } from "../db.js";

const ENGINE = process.env.ENGINE_URL || "http://localhost:8000";
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 15 * 1024 * 1024 } });
const router = Router();

async function callEngine(path, init) {
  try {
    return await fetch(ENGINE + path, init);
  } catch {
    const err = new Error(`Can't reach the detection engine at ${ENGINE}. Start it first (see README).`);
    err.status = 502;
    throw err;
  }
}

async function failFrom(engineRes) {
  const body = await engineRes.json().catch(() => ({}));
  const err = new Error(body.detail || "The detection engine rejected this file.");
  err.status = engineRes.status === 400 || engineRes.status === 413 ? engineRes.status : 502;
  return err;
}

function formFor(req, extra = {}) {
  const form = new FormData();
  form.append("file", new Blob([req.file.buffer]), req.file.originalname);
  for (const [k, v] of Object.entries(extra)) form.append(k, v);
  return form;
}

async function remember(result) {
  if (!db.ready) return null;
  try {
    const doc = await Scan.create({
      filename: result.filename,
      kind: result.kind,
      summary: result.summary,
      findings: result.findings.map(({ type, label, risk, preview }) => ({ type, label, risk, preview })),
    });
    return doc.id;
  } catch (e) {
    console.log("couldn't save scan:", e.message);
    return null;
  }
}

router.post("/scan", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "Choose a file to scan." });
  const r = await callEngine("/api/scan", { method: "POST", body: formFor(req) });
  if (!r.ok) throw await failFrom(r);
  const result = await r.json();
  res.json({ ...result, scanId: await remember(result) });
});

router.post("/scan-text", async (req, res) => {
  const text = String(req.body?.text ?? "");
  if (!text.trim()) return res.status(400).json({ error: "Paste some text to scan." });
  const r = await callEngine("/api/scan-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!r.ok) throw await failFrom(r);
  const result = await r.json();
  res.json({ ...result, scanId: await remember(result) });
});

router.post("/redact", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "Choose a file to redact." });
  const r = await callEngine("/api/redact", {
    method: "POST",
    body: formFor(req, { exclude: req.body.exclude || "[]" }),
  });
  if (!r.ok) throw await failFrom(r);
  res
    .set("Content-Type", r.headers.get("content-type"))
    .set("Content-Disposition", r.headers.get("content-disposition") || "attachment")
    .send(Buffer.from(await r.arrayBuffer()));
});

export default router;
