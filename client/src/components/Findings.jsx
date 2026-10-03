import { RISK_NAME, RISK_RANK } from "../lib.js";

export default function Findings({ result, kept, onToggle }) {
  const { summary, findings } = result;
  const sorted = [...findings].sort((a, b) => RISK_RANK[b.risk] - RISK_RANK[a.risk] || a.start - b.start);

  return (
    <aside className="findings">
      <h2 className={`verdict v-${summary.total ? (summary.by_risk.critical ? "critical" : "other") : "clean"}`}>
        {summary.verdict}
      </h2>
      <p className="counts">
        {summary.total === 0
          ? "We didn't spot emails, numbers, keys or IDs. A quick look yourself is still a good idea."
          : Object.entries(summary.by_risk)
              .filter(([, n]) => n)
              .map(([r, n]) => `${n} ${RISK_NAME[r].toLowerCase()}`)
              .join(", ") + ` found. Tap a bar in the document, or a row here, to keep or redact it.`}
      </p>

      <ul>
        {sorted.map((f) => {
          const isKept = kept.has(f.id);
          return (
            <li key={f.id}>
              <button type="button" className={`row ${isKept ? "is-kept" : ""}`} onClick={() => onToggle(f.id)} aria-pressed={!isKept}>
                <span className={`dot r-${f.risk}`} aria-hidden="true" />
                <span className="row-main">
                  <span className="row-label">{f.label}</span>
                  <span className="row-val">{f.preview}</span>
                </span>
                <span className="row-state">{isKept ? "Keeping" : "Redacting"}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
