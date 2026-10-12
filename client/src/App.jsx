import { useRef, useState } from "react";
import { redactFile, scanFile, scanText } from "./api.js";
import DocView from "./components/DocView.jsx";
import Findings from "./components/Findings.jsx";
import History from "./components/History.jsx";
import { SAMPLE, downloadBlob, redactText } from "./lib.js";

const ACCEPT = ".png,.jpg,.jpeg,.webp,.pdf,.docx";
const OUT_EXT = { image: "png", pdf: "pdf", docx: "docx" };

export default function App() {
  const [tab, setTab] = useState("scan");
  const [busy, setBusy] = useState("");          // "" | "scan" | "redact"
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [kept, setKept] = useState(new Set());   // finding ids the user wants to leave alone
  const [drag, setDrag] = useState(false);
  const [copied, setCopied] = useState(false);
  const input = useRef();

  const reset = () => { setResult(null); setFile(null); setKept(new Set()); setError(""); };

  async function run(task, label) {
    setBusy(label); setError("");
    try { setResult(await task()); setKept(new Set()); }
    catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }

  const pick = (f) => { if (!f) return; setFile(f); run(() => scanFile(f), "scan"); };
  const toggle = (id) => setKept((k) => { const n = new Set(k); n.has(id) ? n.delete(id) : n.add(id); return n; });

  async function download() {
    setBusy("redact"); setError("");
    try {
      const blob = await redactFile(file, [...kept]);
      const base = file.name.replace(/\.[^.]+$/, "");
      downloadBlob(blob, `${base}-redacted.${OUT_EXT[result.kind]}`);
    } catch (e) { setError(e.message); }
    finally { setBusy(""); }
  }

  async function copy() {
    await navigator.clipboard.writeText(redactText(text, result.findings, kept));
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  }

  const redactCount = result ? result.findings.length - kept.size : 0;

  return (
    <div className="shell">
      <header>
        <a className="brand" href="/" onClick={(e) => { e.preventDefault(); reset(); setTab("scan"); }}>
          <span className="mark" aria-hidden="true" />PrivyLens
        </a>
        <nav>
          <button className={tab === "scan" ? "on" : ""} onClick={() => setTab("scan")}>Scan</button>
          <button className={tab === "history" ? "on" : ""} onClick={() => setTab("history")}>History</button>
        </nav>
      </header>

      <main>
        {tab === "history" && <History />}

        {tab === "scan" && !result && (
          <section className="start">
            <h1>Check a file before you post it.</h1>
            <p className="lede">
              Drop a screenshot, PDF or Word file, or paste some text. PrivyLens finds emails, phone numbers,
              keys, passwords and ID numbers, and gives you a copy with them blacked out. Files are only held
              in memory while they're scanned.
            </p>

            <div className="entry">
              <div
                className={`drop ${drag ? "over" : ""}`}
                onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)}
                onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
                onClick={() => input.current.click()}
                role="button" tabIndex={0}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current.click()}
              >
                <input ref={input} type="file" accept={ACCEPT} hidden onChange={(e) => pick(e.target.files[0])} />
                {busy === "scan" ? <p>Reading {file?.name}…</p> : (
                  <>
                    <p className="drop-title">Drop a file here</p>
                    <p className="muted">or click to choose. PNG, JPG, PDF or DOCX, up to 15 MB.</p>
                  </>
                )}
              </div>

              <div className="paste">
                <label htmlFor="t">Or paste text</label>
                <textarea id="t" rows={9} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste an email, a log, a config file…" />
                <div className="paste-actions">
                  <button className="primary" disabled={!text.trim() || busy} onClick={() => run(() => scanText(text), "scan")}>
                    {busy === "scan" && !file ? "Scanning…" : "Scan text"}
                  </button>
                  <button className="link" onClick={() => setText(SAMPLE)}>Try an example</button>
                </div>
              </div>
            </div>
            {error && <p className="error" role="alert">{error}</p>}
          </section>
        )}

        {tab === "scan" && result && (
          <section className="workspace">
            <div className="bar-top">
              <div>
                <p className="filename">{result.filename}</p>
                <p className="muted">{redactCount} of {result.findings.length} will be redacted</p>
              </div>
              <div className="actions">
                <button className="link" onClick={reset}>Start over</button>
                {result.kind === "text" ? (
                  <button className="primary" onClick={copy}>{copied ? "Copied" : "Copy redacted text"}</button>
                ) : (
                  <button className="primary" disabled={busy === "redact"} onClick={download}>
                    {busy === "redact" ? "Redacting…" : `Download redacted ${OUT_EXT[result.kind].toUpperCase()}`}
                  </button>
                )}
              </div>
            </div>
            {error && <p className="error" role="alert">{error}</p>}
            <div className="split">
              <DocView result={result} kept={kept} onToggle={toggle} />
              <Findings result={result} kept={kept} onToggle={toggle} />
            </div>
          </section>
        )}
      </main>

      <footer>
        <p>Detection runs on rules and checksums (Luhn for cards, Verhoeff for Aadhaar), so it can miss things. Give the result a look before you share it.</p>
      </footer>
    </div>
  );
}
