"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Reveal, SectionHeading, SpotlightCard } from "@/components/ui";

type Me = {
  user: { id: number; email: string; name: string; picture: string };
  setting: { shop_name: string; upi_vpa: string; payment_gateway: string };
};
type BindInfo = {
  bot: { configured: boolean; ok?: boolean; username?: string; error?: string };
  unbound: { name: string; code: string }[];
};

export default function SettingsPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [bind, setBind] = useState<BindInfo | null>(null);
  const [shopName, setShopName] = useState("");
  const [vpa, setVpa] = useState("");
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const m: Me = await api.get("/me");
      setMe(m);
      setShopName(m.setting.shop_name);
      setVpa(m.setting.upi_vpa);
      api.get("/telegram/bind-info").then(setBind).catch(() => {});
    } catch (e) {
      router.replace("/");
      return;
    }
  }
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function save() {
    setSaving(true);
    setError("");
    try {
      await api.patch("/me/settings", { shop_name: shopName, upi_vpa: vpa });
      setFlash("save ho gaya ✅");
      load();
    } catch (e) {
      setError(String(e));
    }
    setSaving(false);
  }

  async function refreshTelegram() {
    setError("");
    try {
      await api.post("/telegram/refresh");
      await load();
      setFlash("telegram check ho gaya ✅");
    } catch (e) {
      setError(String(e));
    }
  }

  async function refreshBinds() {
    setError("");
    try {
      const b: BindInfo = await api.get("/telegram/bind-info");
      setBind(b);
      await api.post("/telegram/refresh").catch(() => {});
      const after: BindInfo = await api.get("/telegram/bind-info");
      setBind(after);
      setFlash("bindaya hua check ho gaya ✅");
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="space-y-10">
      <Reveal>
        <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-[var(--faint)]">
          settings
        </p>
        <h1 className="font-display mt-2 text-4xl">dukaan ki setting</h1>
      </Reveal>

      <section className="grid gap-4 md:grid-cols-2">
        <SpotlightCard>
          <div className="p-6">
            <p className="label">profile</p>
            {me && (
              <>
                <p className="font-display text-2xl">{me.user.name}</p>
                <p className="mt-1 font-mono text-[11px] text-[var(--muted)]">{me.user.email}</p>
              </>
            )}
          </div>
        </SpotlightCard>
        <SpotlightCard>
          <div className="p-6">
            <p className="label">payments</p>
            <p className="text-[13.5px] leading-relaxed text-[var(--muted)]">
              UPI ID deni hai (e.g. <code className="font-mono text-[var(--ink)]">owner@upi</code>) — receipt ka
              upi://pay link isi par jayega. Gateway integration (Razorpay) band keys aapke paas hon chahiye —
              agar aapke keys me mileuin, phir payment tracking webhook ke saath automatic hoga.
            </p>
          </div>
        </SpotlightCard>
      </section>

      <section>
        <SectionHeading kicker="dukaan" title="shop ka naam aur UPI" />
        <Reveal>
          <SpotlightCard>
            <div className="space-y-4 p-6">
              <div>
                <label className="label" htmlFor="shop">dukaan ka naam</label>
                <input className="input" id="shop" value={shopName} onChange={(e) => setShopName(e.target.value)} placeholder="Sharma General Store" />
              </div>
              <div>
                <label className="label" htmlFor="vpa">UPI ID (baaki mein payment link isi par jayega)</label>
                <input className="input font-mono" id="vpa" value={vpa} onChange={(e) => setVpa(e.target.value)} placeholder="owner@upi" />
              </div>
              <div className="flex items-center gap-3">
                <button className="btn btn-primary" onClick={save} disabled={saving || !me}>
                  {saving ? "save ho raha hai…" : "save"}
                </button>
                {flash && <p className="font-mono text-xs text-[var(--ok)]">{flash}</p>}
              </div>
              {error && (
                <p className="rounded-lg border border-[rgba(224,140,123,0.3)] bg-[rgba(224,140,123,0.07)] p-3 font-mono text-xs text-[var(--bad)]">
                  {error}
                </p>
              )}
            </div>
          </SpotlightCard>
        </Reveal>
      </section>

      <section>
        <SectionHeading kicker="telegram" title="receipt delivery" />
        <Reveal>
          <SpotlightCard>
            <div className="space-y-4 p-6">
              {bind?.bot.configured ? (
                <>
                  <p className="text-[13.5px] leading-relaxed text-[var(--ink)]">
                    Bot <span className="font-mono text-[var(--accent)]">@{bind.bot.username}{" "}</span>
                    {bind.bot.ok ? (
                      <span className="text-[var(--ok)]">live hai — /bind codon ke liye sun raha hai.</span>
                    ) : (
                      <span className="text-[var(--bad)]">{bind.bot.error ?? "token problem"}</span>
                    )}
                  </p>
                  {(bind.unbound?.length || 0) === 0 ? (
                    <p className="text-[13px] text-[var(--muted)]">Sab customers bound hain.</p>
                  ) : (
                    <div className="space-y-2">
                      {bind.unbound.map((u) => (
                        <div key={u.code} className="flex items-baseline justify-between rounded-lg border border-[var(--line)] px-4 py-2.5">
                          <span className="font-display text-lg">{u.name}</span>
                          <code className="rounded bg-[var(--panel-2)] px-2 py-1 font-mono text-[13px] text-[var(--accent)]">
                            /bind {u.code}
                          </code>
                        </div>
                      ))}
                    </div>
                  )}
                  <button className="btn btn-ghost" onClick={refreshBinds}>
                    bind check karein
                  </button>
                  <button className="btn btn-ghost" onClick={refreshTelegram}>
                    bot status refresh
                  </button>
                </>
              ) : (
                <p className="text-[13.5px] leading-relaxed text-[var(--muted)]">
                  Bot token set nahi hai. @BotFather se token lekar <code className="font-mono text-[var(--ink)]">.env</code> mein
                  <code className="mx-1 font-mono text-[var(--ink)]">TELEGRAM_BOT_TOKEN=</code> dalein aur backend
                  restart karein.
                </p>
              )}
            </div>
          </SpotlightCard>
        </Reveal>
      </section>

      <section>
        <SectionHeading kicker="account" title="sign out" />
        <Reveal>
          <button
            className="btn btn-ghost"
            onClick={async () => {
              await api.post("/auth/logout");
              location.href = "/";
            }}
          >
            sign out
          </button>
        </Reveal>
      </section>
    </div>
  );
}
