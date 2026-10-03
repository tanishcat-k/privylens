async function parse(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed (${res.status})`);
  }
  return res;
}

export async function scanFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await parse(await fetch("/api/scan", { method: "POST", body: form }));
  return res.json();
}

export async function scanText(text) {
  const res = await parse(
    await fetch("/api/scan-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    })
  );
  return res.json();
}

export async function redactFile(file, keepIds) {
  const form = new FormData();
  form.append("file", file);
  form.append("exclude", JSON.stringify(keepIds));
  const res = await parse(await fetch("/api/redact", { method: "POST", body: form }));
  return res.blob();
}

export async function getHistory() {
  return (await parse(await fetch("/api/history"))).json();
}

export async function deleteScan(id) {
  await parse(await fetch(`/api/history/${id}`, { method: "DELETE" }));
}

export async function clearHistory() {
  await parse(await fetch("/api/history", { method: "DELETE" }));
}
