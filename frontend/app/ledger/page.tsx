"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { api, LANG_LABEL } from "@/lib/api";
import { Reveal, SectionHeading, SpotlightCard, StatusBadge } from "@/components/ui";

type Customer = {
  id: number; name: string; due: number; unpaid_bills: number;
  telegram_bound: boolean; telegram_username?: string | null;
};
type Recent = {
  id: number; customer: string; total: number; payment_status: string;
  item_count: number; created_at: string;
};

const rupees = (v: number) => `₹${v % 1 === 0 ? v.toFixed(0) : v.toFixed(2)}`;

export default function LedgerPage() {
  const [customers, setCustomers] = useState<Customer[] | null>(null);
  const [recents, setRecents] = useState<Recent[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/me").catch(() => (location.href = "/"));
    api.get("/customers").then((r) => setCustomers(r.customers)).catch((e) => setError(String(e)));
    api.get("/bills/recent").then((r) => setRecents(r.bills)).catch(() => {});
  }, []);

  const totalDue = (customers || []).reduce((s, c) => s + (c.due || 0), 0);
  const settled = recents?.filter((b) => b.payment_status === "paid").length ?? 0;

  return (
    <div className="space-y-11">
      <Reveal>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.24em] text-[var(--faint)]">
              aaj ka khaata
            </p>
            <h1 className="font-display mt-1 text-4xl">
              {customers === null ? "…" : <>baaki <span className="text-[var(--accent)]">{rupees(totalDue || 0)}</span></>}
            </h1>
          </div>
          <Link href="/speak" className="btn btn-primary">
            ◉ bolo se entry karein
          </Link>
        </div>
      </Reveal>

      {error && (
        <p className="rounded-lg border border-[rgba(224,140,123,0.3)] bg-[rgba(224,140,123,0.07)] p-3 font-mono text-xs text-[var(--bad)]">
          {error}
        </p>
      )}

      {/* customers */}
      <section>
        <SectionHeading kicker="khaata" title="customers" >
          <p className="mt-1 text-[13px] text-[var(--muted)]">
            Boore se kisi ka naam bola, aur wo khud register ho jata hai. Telegram wala dot = receipt bound.
          </p>
        </SectionHeading>
        {customers === null ? (
          <p className="font-mono text-xs text-[var(--muted)]">loading…</p>
        ) : customers.length === 0 ? (
          <SpotlightCard>
            <div className="p-8 text-center">
              <p className="font-display text-2xl">khali khaata</p>
              <p className="mt-2 text-[13.5px] text-[var(--muted)]">
                Pehli entry Speak screen se boliye — customer khud ban jayega.
              </p>
              <Link href="/speak" className="btn btn-primary mt-5">bole shuru karein</Link>
            </div>
          </SpotlightCard>
        ) : (
          <div className="space-y-3">
            {customers.map((c, i) => (
              <Reveal key={c.id} delay={Math.min(i * 0.04, 0.3)}>
                <motion.div layout>
                  <SpotlightCard>
                    <Link href={`/customers/${c.id}`} className="block p-5">
                      <div className="flex flex-wrap items-baseline justify-between gap-3">
                        <div>
                          <p className="font-display text-xl">{c.name}</p>
                          <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--faint)]">
                            {c.unpaid_bills} unpaid · {c.telegram_bound ? "telegram ✓" : "telegram ✗"}
                          </p>
                        </div>
                        <p className={`font-display text-2xl ${c.due > 0 ? "text-[var(--warn)]" : "text-[var(--ok)]"}`}>
                          {c.due > 0 ? rupees(c.due) : "settled"}
                        </p>
                      </div>
                    </Link>
                  </SpotlightCard>
                </motion.div>
              </Reveal>
            ))}
          </div>
        )}
      </section>

      {/* recent bills */}
      {recents && recents.length > 0 && (
        <section>
          <SectionHeading kicker="recent" title={`${settled}/${recents.length} recent darj se pura hue`} />
          <div className="space-y-3">
            {recents.map((b, i) => (
              <Reveal key={b.id} delay={Math.min(i * 0.04, 0.3)}>
                <SpotlightCard>
                  <div className="flex flex-wrap items-baseline justify-between gap-3 p-4">
                    <div>
                      <p className="font-display text-lg">{b.customer}</p>
                      <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--faint)]">
                        bill #{b.id} · {b.item_count} cheez · {b.created_at.slice(0, 10)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <StatusBadge status={b.payment_status === "paid" ? "succeeded" : "queued"} />
                      <p className="font-display text-xl">{rupees(b.total)}</p>
                    </div>
                  </div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
