// The document itself, with every finding as a clickable bar.
// Black bar = will be redacted. Yellow = you chose to keep it.

function Hit({ f, kept, onToggle, children, style, className = "" }) {
  return (
    <button
      type="button"
      className={`hit ${kept ? "kept" : "bar"} ${className}`}
      style={style}
      onClick={() => onToggle(f.id)}
      aria-pressed={!kept}
      title={`${f.label}: ${kept ? "kept, click to redact" : "redacted, click to keep"}`}
    >
      {children}
    </button>
  );
}

function Segments({ text, findings, kept, onToggle }) {
  const parts = [];
  let last = 0;
  for (const f of [...findings].sort((a, b) => a.start - b.start)) {
    if (f.start > last) parts.push(<span key={`t${last}`}>{text.slice(last, f.start)}</span>);
    const isKept = kept.has(f.id);
    // redacted values are never put in the DOM, just a same-width bar
    const shown = isKept ? text.slice(f.start, f.end) : "\u2007".repeat(Math.min(f.end - f.start, 48));
    parts.push(
      <Hit key={f.id} f={f} kept={isKept} onToggle={onToggle}>
        {shown}
      </Hit>
    );
    last = f.end;
  }
  parts.push(<span key="end">{text.slice(last)}</span>);
  return parts;
}

export default function DocView({ result, kept, onToggle }) {
  if (result.pages) {
    return (
      <div className="pages">
        {result.pages.map((p, i) => (
          <div className="page" key={i}>
            {result.pages.length > 1 && <p className="page-no">Page {i + 1}</p>}
            <div className="page-img">
              <img src={p.image} alt={`Page ${i + 1} of ${result.filename}`} />
              {result.findings
                .filter((f) => f.page === i)
                .flatMap((f) =>
                  f.boxes.map(([x, y, w, h], j) => (
                    <Hit
                      key={`${f.id}-${j}`}
                      f={f}
                      kept={kept.has(f.id)}
                      onToggle={onToggle}
                      className="box"
                      style={{ left: `${x * 100 - 0.3}%`, top: `${y * 100 - 0.3}%`, width: `${w * 100 + 0.6}%`, height: `${h * 100 + 0.6}%` }}
                    />
                  ))
                )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="text-doc">
      {result.blocks.map((b) => (
        <p key={b.id}>
          <Segments
            text={b.text}
            findings={result.findings.filter((f) => f.block === b.id)}
            kept={kept}
            onToggle={onToggle}
          />
        </p>
      ))}
    </div>
  );
}
