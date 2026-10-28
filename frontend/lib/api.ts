export const API =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request(path: string, init?: RequestInit) {
  const res = await fetch(`${API}/api${path}`, {
    cache: "no-store",
    credentials: "include",
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {}
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  get: (path: string) => request(path),
  post: (path: string, body?: unknown) =>
    request(path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: (path: string, body: unknown) =>
    request(path, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    }),
  del: (path: string) => request(path, { method: "DELETE" }),
};

export const LANG_LABEL: Record<string, string> = {
  hi: "HI", ta: "TA", mr: "MR", kn: "KN", en: "EN", te: "TE", bn: "BN",
};

export const STATUS_STYLE: Record<string, string> = {
  succeeded: "bg-emerald-900/60 text-emerald-300",
  failed: "bg-rose-900/60 text-rose-300",
  running: "bg-sky-900/60 text-sky-300",
  queued: "bg-lab-700 text-gray-300",
};
