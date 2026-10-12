import mongoose from "mongoose";

// We never store the uploaded file or the raw sensitive values,
// only what's needed to show "you scanned X and it had Y".
const findingSchema = new mongoose.Schema(
  { type: String, label: String, risk: String, preview: String },
  { _id: false }
);

const scanSchema = new mongoose.Schema(
  {
    filename: { type: String, required: true },
    kind: { type: String, enum: ["image", "pdf", "docx", "text"], required: true },
    summary: {
      total: Number,
      verdict: String,
      by_risk: { critical: Number, high: Number, medium: Number, low: Number },
    },
    findings: [findingSchema],
  },
  { timestamps: true }
);

export default mongoose.model("Scan", scanSchema);
