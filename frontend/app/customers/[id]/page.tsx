"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, LANG_LABEL } from "@/lib/api";
import { Counter, Reveal, SectionHeading, SpotlightCard } from "@/components/ui";

type Item = { name: string; qty: number; unit: string; price: number | null };
type Bill = {
  id: number; items: Item[]; total: number; payment_status: string;
  payment_link: string; telegram_sent: boolean; raw_transcript: string;
  notes: string; created_at: string;
};
type Data = {
  customer: { id: number; name: string; bind_code: string; telegram_bound: boolean; telegram_username?: string | null };
  bills: Bill[];
};

const rupees = (v: number | null) =>
  v == null ? "—" : `₹${v % 1 === 0 ? v.toFixed(0) : v.toFixed(2)}`;

export default function CustomerPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  async function load() {
    try {
      setData(await api.get(`/customers/${id}/bills`));
    } catch (e) {
      setError(String(e));
    }
  }
  useEffect(() => {
    if (id) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (error)
    return (
      <p className="rounded-lg border border-[rgba(224,140,123,0.3)] bg-[rgba(224,140,123,0.07)] p-3 font-mono text-xs text-[var(--bad)]">
        {error}
      </p>
    );
  if (!data) return <p className="font-mono text-xs text-[var(--muted)]">loading…</p>;

  const { customer, bills } = data;
  const due = bills
    .filter((b) => b.payment_status !== "paid")
    .reduce((s, b) => s + b.total, 0);

  async function markPaid(bill: Bill) {
    setError("");
    try {
      const r = await api.post(`/bills/${bill.id}/mark-paid`);
      setFlash(r.bill.payment_status === "paid" ? "bill paid ✅" : "bill dubara unpaid");
      load();
    } catch (e) {
      setError(String(e));
      setFlash("");
    }
  }

  async function sendTelegram(bill: Bill) {
    setError("");
    setFlash("Telegram par bhej raha hai…");
    try {
      const r = await api.post(`/bills/${bill.id}/send-telegram`);
      setFlash(`receipt bhej diya ✅ → ${r.chat}`);
      load();
    } catch (e) {
      setError(String(e));
      setFlash("");
    }
  }

  function copyLink(bill: Bill) {
    navigator.clipboard.writeText(bill.payment_link);
    setFlash("UPI link copy ho gaya — kisi bhi chat mein chipka sakte hain");
  }

  return (
    <div className="space-y-10">
      <Reveal>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Link
              href="/ledger"
              className="font-mono text-[10px] uppercase tracking-[0.24em] text-[var(--faint)] hover:text-[var(--muted)]"
            >
              ← khaata
            </Link>
            <h1 className="font-display mt-1 text-4xl">{customer.name}</h1>
            <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--faint)]">
              {customer.telegram_bound
                ? `telegram bound${customer.telegram_username ? ` (@${customer.telegram_username})` : ""}`
                : `telegram not bound · code ${customer.bind_code}`}
            </p>
          </div>
          <div className="text-right">
            <p className="label mb-1">baaki</p>
            <p
              className="font-display text-3xl"
              style={{ color: due > 0 ? "var(--warn)" : "var(--ok)" }}
            >
              <Counter value={due} format={(v) => rupees(v)} />
            </p>
          </div>
        </div>
        {flash && <p className="mt-3 font-mono text-xs text-[var(--ok)]">{flash}</p>}
        {!customer.telegram_bound && (
          <p className="mt-3 rounded-lg border border-[rgba(217,179,107,0.3)] bg-[rgba(217,179,107,0.06)] p-3 text-[12.5px] leading-relaxed text-[var(--warn)]">
            Customer ko apne bot par{" "}
            <code className="rounded bg-[var(--panel-2)] px-1.5 py-0.5 font-mono">
              /bind {customer.bind_code}
            </code>{" "}
            bhejne ko kahein — uske baad isi chat par receipts aayengi.
          </p>
        )}
      </Reveal>

      <section className="space-y-4">
        <SectionHeading kicker="history" title="bills" />
        {bills.length === 0 && (
          <p className="text-[13px] text-[var(--muted)]">
            Khi entry nahi.{" "}
            <Link href="/speak" className="text-[var(--accent)]">
              bolo se shuru karein →
            </Link>
          </p>
        )}
        {bills.map((b, i) => (
          <Reveal key={b.id} delay={Math.min(i * 0.05, 0.4)}>
            <SpotlightCard>
              <div className="space-y-4 p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                  <div>
                    <p className="font-display text-2xl">{rupees(b.total)}</p>
                    <p className="mt-0.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--faint)]">
                      bill #{b.id} ·{" "}
                      <span style={{ color: b.payment_status === "paid" ? "var(--ok)" : "var(--warn)" }}>
                        {b.payment_status === "paid" ? "paid ✓" : "unpaid"}
                      </span>
                      {b.telegram_sent && " · telegram ✓"} · {b.created_at.slice(0, 10)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button className="btn btn-ghost" onClick={() => markPaid(b)}>
                      {b.payment_status === "paid" ? "unpaid karein" : "paid mark karein"}
                    </button>
                    {b.payment_link && (
                      <button className="btn btn-ghost" onClick={() => copyLink(b)}>
                        pay link copy
                      </button>
                    )}
                    <button
                      className="btn btn-primary"
                      onClick={() => sendTelegram(b)}
                      disabled={!customer.telegram_bound}
                    >
                      {b.telegram_sent ? "dubara bhejein" : "telegram par bhejein"}
                    </button>
                  </div>
                </div>
                {b.notes && (
                  <p className="font-mono text-[11px] text-[var(--warn)]">note: {b.notes}</p>
                )}
                <table className="w-full text-[13px]">
                  <tbody>
                    {b.items.map((it, j) => (
                      <tr key={j} className="border-t border-[var(--line)]">
                        <td className="py-1.5">{it.name}</td>
                        <td className="py-1.5 font-mono text-[var(--muted)]">
                          {it.qty % 1 === 0 ? it.qty.toFixed(0) : it.qty}
                          {it.unit && ` ${it.unit}`}
                        </td>
                        <td className="py-1.5 text-right font-mono">{rupees(it.price)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {b.raw_transcript && (
                  <p className="hindi-tamil border-t border-dashed border-[var(--line)] pt-2 font-mono text-[10.5px] leading-relaxed text-[var(--faint)]">
                    spoken: {b.raw_transcript}
                  </p>
                )}
              </div>
            </SpotlightCard>
          </Reveal>
        ))}
      </section>
    </div>
  );
}
