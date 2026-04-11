const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadContent(
  file: File | null,
  url: string | null,
  platform: string,
  caption: string
) {
  const form = new FormData();
  if (file) form.append("file", file);
  if (url) form.append("url", url);
  form.append("platform", platform);
  form.append("caption", caption);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runSimulation(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/simulate/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getInterpretation(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/interpret/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function streamInterpretation(sessionId: string) {
  return new EventSource(`${API_BASE}/api/interpret/${sessionId}/stream`);
}

export async function runPolishing(
  sessionId: string,
  approvedIds: string[],
  caption: string,
  platform: string
) {
  const res = await fetch(`${API_BASE}/api/polish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      approved_suggestion_ids: approvedIds,
      caption,
      platform,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runComparison(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/compare/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
