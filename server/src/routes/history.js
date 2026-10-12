import { Router } from "express";
import Scan from "../models/Scan.js";
import { db } from "../db.js";

const router = Router();

router.get("/", async (_req, res) => {
  if (!db.ready) return res.json({ enabled: false, scans: [] });
  const scans = await Scan.find().sort({ createdAt: -1 }).limit(50).lean();
  res.json({ enabled: true, scans });
});

router.delete("/:id", async (req, res) => {
  if (db.ready) await Scan.findByIdAndDelete(req.params.id);
  res.status(204).end();
});

router.delete("/", async (_req, res) => {
  if (db.ready) await Scan.deleteMany({});
  res.status(204).end();
});

export default router;
