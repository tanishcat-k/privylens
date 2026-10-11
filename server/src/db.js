import mongoose from "mongoose";

// History is a nice-to-have. If Mongo is down the scanner still works.
export const db = { ready: false };

export async function connectDb() {
  const uri = process.env.MONGODB_URI;
  if (!uri) return console.log("MONGODB_URI not set, history is off.");
  try {
    await mongoose.connect(uri, { serverSelectionTimeoutMS: 4000 });
    db.ready = true;
    console.log("MongoDB connected");
  } catch (e) {
    console.log("MongoDB not reachable, history is off:", e.message);
  }
}
