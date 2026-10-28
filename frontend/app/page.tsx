"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Reveal, SectionHeading, SpotlightCard } from "@/components/ui";

type AuthConfig = {
  google: boolean;
  client_id: string;
  dev_login: boolean;
  telegram: { configured: boolean; ok?: boolean; username?: string; error?: string };
};

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (cfg: { client_id: string; callback: (r: { credential: string }) => void }) => void;
          renderButton: (el: HTMLElement, opts: Record<string, unknown>) => void;
        };
      };
    };
  }
}

export default function LoginPage() {
  const router = useRouter();
  const [cfg, setCfg] = useState<AuthConfig | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const gsiRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get("/me")
      .then(() => router.replace("/ledger"))
      .catch(() => api.get("/auth/config").then(setCfg).catch((e) => setError(String(e))));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!cfg?.google || !gsiRef.current) return;
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => {
      if (!window.google || !gsiRef.current) return;
      window.google.accounts.id.initialize({
        client_id: cfg.client_id,
        callback: async (response) => {
          setBusy(true);
          setError("");
          try {
            await api.post("/auth/google", { credential: response.credential });
            router.replace("/ledger");
          } catch (e) {
            setError(String(e));
            setBusy(false);
          }
        },
      });
      window.google.accounts.id.renderButton(gsiRef.current, {
        theme: "filled_black",
        size: "large",
        shape: "pill",
        text: "continue_with",
        width: 260,
      });
    };
    document.head.appendChild(script);
    return () => { document.head.removeChild(script); };
  }, [cfg, router]); // eslint-disable-line react-hooks/exhaustive-deps

  async function devLogin() {
    setBusy(true);
    setError("");
    try {
      await api.post("/auth/dev");
      router.replace("/ledger");
    } catch (e) {
      setError(String(e));
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-[70vh] place-items-center">
      <div className="w-full max-w-md space-y-8 text-center">
        <Reveal>
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-[var(--faint)]">
            voice khaata · zero typing
          </p>
          <h1 className="font-display mt-3 text-5xl leading-tight">
            Bolo <span className="text-[var(--accent)]">Khata</span>
          </h1>
          <p className="mt-4 text-[14px] leading-relaxed text-[var(--muted)]">
            <span className="text-[var(--ink)]">Bole bharo</span> — “Sharma ji doodh 1 packet ₹30…”
            <br />
            and it lands in the ledger, on Telegram, with a pay link.
          </p>
        </Reveal>

        <Reveal delay={0.1}>
          <SpotlightCard>
            <div className="space-y-5 p-7">
              {busy && (
                <p className="animate-pulse font-mono text-xs text-[var(--muted)]">signing you in…</p>
              )}
              {cfg?.google && <div className="flex justify-center" ref={gsiRef} />}
              {cfg?.dev_login && (
                <button className="btn btn-ghost w-full" onClick={devLogin} disabled={busy}>
                  try the demo owner (dev login)
                </button>
              )}
              {cfg && !cfg.google && !cfg.dev_login && (
                <p className="font-mono text-xs text-[var(--warn)]">
                  Neither GOOGLE_CLIENT_ID nor dev login is configured on the server.
                </p>
              )}
              {error && (
                <p className="rounded-lg border border-[rgba(224,140,123,0.3)] bg-[rgba(224,140,123,0.07)] p-3 font-mono text-xs text-[var(--bad)]">
                  {error}
                </p>
              )}
            </div>
          </SpotlightCard>
        </Reveal>

        <Reveal delay={0.18}>
          <p className="mx-auto max-w-sm font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--faint)]">
            हिंदी · हिंग्लिश · मराठी · तमिल · કન્નડ · english
          </p>
        </Reveal>
      </div>
    </div>
  );
}
