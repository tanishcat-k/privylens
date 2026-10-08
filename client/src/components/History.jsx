import { useEffect, useState } from "react";
import { clearHistory, deleteScan, getHistory } from "../api.js";
import { RISK_NAME, timeAgo } from "../lib.js";

export default function History() {
  const [state, setState] = useState({ loading: true, enabled: true, scans: [], error: "" });

  const load = () =>
    getHistory()
      .then((d) => setState({ loading: false, enabled: d.enabled, scans: d.scans, error: "" }))
      .catch((e) => setState({ loading: false, enabled: true, scans: [], error: e.message }));

  useEffect(() => { load(); }, []);

  if (state.loading) return <p className="muted">Loading…</p>;
  if (state.error) return <p className="error">{state.error}</p>;
  if (!state.enabled)
    return <p className="muted">History needs MongoDB, and the server couldn't connect to it. Scanning still works. Set <code>MONGODB_URI</code> in <code>server/.env</code> and restart.</p>;
  if (!state.scans.length)
    return <p className="muted">Nothing here yet. Scans you run will show up with what was found, never the files or the actual values.</p>;

  return (
    <div className="history">
      <div className="history-head">
        <p className="muted">We keep the file name and masked samples only.</p>
        <button className="link" onClick={async () => { await clearHistory(); load(); }}>Clear all</button>
      </div>
      <ul>
        {state.scans.map((s) => (
          <li key={s._id}>
            <div>
              <strong>{s.filename}</strong>
              <span className="muted"> · {s.kind} · {timeAgo(s.createdAt)}</span>
              <p>{s.summary.verdict}</p>
              <p className="muted">
                {Object.entries(s.summary.by_risk).filter(([, n]) => n).map(([r, n]) => `${n} ${RISK_NAME[r].toLowerCase()}`).join(", ") || "no findings"}
              </p>
            </div>
            <button className="link" onClick={async () => { await deleteScan(s._id); load(); }}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
