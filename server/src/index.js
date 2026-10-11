import "dotenv/config";
import cors from "cors";
import express from "express";
import { connectDb, db } from "./db.js";
import historyRoutes from "./routes/history.js";
import scanRoutes from "./routes/scan.js";

const app = express();

app.use(cors({ origin: (process.env.CLIENT_URL || "http://localhost:5173").split(",") }));
app.use(express.json({ limit: "1mb" }));

app.get("/api/health", (_req, res) => res.json({ ok: true, history: db.ready }));
app.use("/api", scanRoutes);
app.use("/api/history", historyRoutes);

// Express 5 forwards async errors here
app.use((err, _req, res, _next) => {
  if (err.code === "LIMIT_FILE_SIZE") return res.status(413).json({ error: "Files can be 15 MB at most." });
  if (!err.status) console.error(err);
  res.status(err.status || 500).json({ error: err.message || "Something went wrong." });
});

const port = process.env.PORT || 5000;
connectDb().finally(() => app.listen(port, () => console.log(`PrivyLens API on :${port}`)));
