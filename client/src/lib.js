export const RISK_RANK = { critical: 4, high: 3, medium: 2, low: 1 };
export const RISK_NAME = { critical: "Critical", high: "High", medium: "Medium", low: "Low" };

export const SAMPLE = `Hi Priya, sending the details for the hostel form.

Email: tanishka@example.com
Phone: 9876543210
Aadhaar: 2345 6789 0124
PAN: ABCPD1234E
Card: 4111 1111 1111 1111

Staging login is admin / password = hunter2hunter
AWS key: AKIAIOSFODNN7EXAMPLE
Callback: https://app.site.io/cb?access_token=abcd1234efgh&x=1`;

// Rebuild text with [REDACTED] in place of every finding the user hasn't kept.
export function redactText(text, findings, kept) {
  let out = "";
  let last = 0;
  for (const f of [...findings].sort((a, b) => a.start - b.start)) {
    if (kept.has(f.id)) continue;
    out += text.slice(last, f.start) + "[REDACTED]";
    last = f.end;
  }
  return out + text.slice(last);
}

export function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function timeAgo(iso) {
  const mins = Math.round((Date.now() - new Date(iso)) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}
