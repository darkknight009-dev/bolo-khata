"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { api, LANG_LABEL } from "@/lib/api";
import { blobToB64, Recorder, startRecording } from "@/lib/wav";
import { Reveal, SpotlightCard } from "@/components/ui";

type Item = { name: string; qty: number; unit: string; price: number | null };
type Entry = {
  customer: string;
  customer_id: number | null;
  customer_matched: string | null;
  language: string;
  items: Item[];
  total: number;
  notes: string;
  transcript: string;
};

type Phase = "idle" | "recording" | "transcribing" | "reviewing" | "saving" | "done";

const rupees = (v: number | null | undefined) =>
  v == null ? "—" : `₹${v % 1 === 0 ? v.toFixed(0) : v.toFixed(2)}`;

export default function SpeakPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("idle");
  const [pushMode, setPushMode] = useState(false); // double-tap continuous listening
  const [transcript, setTranscript] = useState("");
  const [entry, setEntry] = useState<Entry | null>(null);
  const [error, setError] = useState("");
  const [savedBill, setSavedBill] = useState<{ id: number; customer_id: number; total: number } | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const recorderRef = useRef<Recorder | null>(null);
  const lastTapRef = useRef(0);
  const holdRef = useRef(false);

  useEffect(() => {
    api.get("/me").catch(() => router.replace("/"));
  }, [router]); // eslint-disable-line react-hooks/exhaustive-deps

  const finishHold = useCallback(async () => {
    const recorder = recorderRef.current;
    if (!recorder) return;
    recorderRef.current = null;
    setPhase("transcribing");
    try {
      const wav = await recorder.stop();
      const audio_b64 = await blobToB64(wav);
      const stt = await api.post("/transcribe", { audio_b64 });
      setTranscript(stt.text || "");
      const parsed = await api.post("/entries", { transcript: stt.text });
      setEntry(parsed.entry);
      setPhase("reviewing");
    } catch (e) {
      setError(String(e));
      setPhase("idle");
      setPushMode(false);
    }
  }, []);

  const startHold = useCallback(async () => {
    if (recorderRef.current) return;
    setError("");
    setEntry(null);
    setTranscript("");
    setSavedBill(null);
    setElapsed(0);
    try {
      recorderRef.current = await startRecording();
      setPhase("recording");
    } catch (e) {
      setError("Mic nahi khula: " + String(e));
      setPhase("idle");
    }
  }, []);

  // push-mode: keep recording until a single tap stops it
  useEffect(() => {
    if (!pushMode) return;
    startHold().then(() => setPhase("recording"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pushMode]);

  useEffect(() => {
    if (phase !== "recording") return;
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [phase]);

  function onOrbPointerDown() {
    holdRef.current = true;
    const now = Date.now();
    const isDoubleTap = now - lastTapRef.current < 300;
    lastTapRef.current = now;
    if (phase === "recording" && pushMode) {
      // second tap in mode -> stop
      setPushMode(false);
      finishHold();
      return;
    }
    if (isDoubleTap) {
      setPushMode(true); // triggers start via effect
      return;
    }
    startHold();
  }

  function onOrbPointerUp() {
    if (pushMode || phase !== "recording") {
      holdRef.current = false;
      return;
    }
    holdRef.current = false;
    finishHold();
  }

  async function save() {
    if (!entry) return;
    setPhase("saving");
    setError("");
    try {
      const res = await api.post("/bills", {
        customer_name: entry.customer_matched || entry.customer,
        transcript: entry.transcript,
        items: entry.items,
        total: entry.total,
        language: entry.language,
        notes: entry.notes,
      });
      setSavedBill({
        id: res.bill.id,
        customer_id: res.customer.id,
        total: res.bill.total,
      });
      setPhase("done");
    } catch (e) {
      setError(String(e));
      setPhase("reviewing");
    }
  }

  const mm = (s: number) => `0:${String(s % 60).padStart(2, "0")}`;

  return (
    <div className="select-none space-y-8">
      {/* orb */}
      <div className="grid place-items-center py-6">
        <motion.button
          aria-label="hold to speak"
          onPointerDown={onOrbPointerDown}
          onPointerUp={onOrbPointerUp}
          onPointerLeave={() => phase === "recording" && !pushMode && holdRef.current && onOrbPointerUp()}
          whileTap={{ scale: 0.96 }}
          animate={
            phase === "recording"
              ? { boxShadow: "0 0 0 0px rgba(228,168,83,0.55)" }
              : { boxShadow: "0 0 0 0px rgba(228,168,83,0)" }
          }
          className="grid h-52 w-52 place-items-center rounded-full border border-[var(--line)] bg-[var(--panel)]"
        >
          {phase === "recording" ? (
            <motion.span
              className="grid h-40 w-40 place-items-center rounded-full bg-[rgba(228,168,83,0.10)]"
              animate={{ boxShadow: ["0 0 0 0px rgba(228,168,83,0.45)", "0 0 0 22px rgba(228,168,83,0)"] }}
              transition={{ repeat: Infinity, duration: 1.4, ease: "easeOut" }}
            >
              <span className="font-mono text-xs text-[var(--accent)]">{mm(elapsed)}</span>
            </motion.span>
          ) : (
            <svg width="72" height="72" viewBox="0 0 24 24" fill="none" aria-hidden>
              <rect x="9" y="3" width="6" height="11" rx="3" fill="var(--accent)" />
              <path d="M6 11.5a6 6 0 0 0 12 0" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M12 17v3M8.5 21h7" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          )}
        </motion.button>
        <p className="mt-5 text-center font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
          {phase === "idle" && "dabaye aur boliye — hold to speak"}
          {phase === "recording" && (pushMode ? "tap once to stop" : "release to stop")}
          {phase === "transcribing" && "sun raha hoon… taq addad pehchan raha hai"}
          {phase === "reviewing" && "galti ho to seedha karein, phir save karein"}
          {phase === "saving" && "khaata mein darj…"}
          {phase === "done" && "darj ho gaya ✅"}
        </p>
        <p className="mt-1 font-mono text-[10px] text-[var(--faint)]">
          double-tap = continuous mode
        </p>
      </div>

      {error && (
        <p className="rounded-lg border border-[rgba(224,140,123,0.3)] bg-[rgba(224,140,123,0.07)] p-3 font-mono text-xs text-[var(--bad)]">
          {error}
        </p>
      )}

      {savedBill && (
        <Reveal>
          <SpotlightCard>
            <div className="p-6 text-center">
              <p className="font-display text-3xl">{rupees(savedBill.total)}</p>
              <p className="label mt-2">bill #{savedBill.id} · darj ho gaya</p>
              <div className="mt-4 flex flex-wrap justify-center gap-3">
                <Link href={`/customers/${savedBill.customer_id}`} className="btn btn-primary">
                  receipt bhejein →
                </Link>
                <button className="btn btn-ghost" onClick={() => { setPhase("idle"); setSavedBill(null); setEntry(null); setTranscript(""); }}>
                  nayi entry
                </button>
              </div>
            </div>
          </SpotlightCard>
        </Reveal>
      )}

      {/* review card */}
      {entry && phase !== "done" && (
        <Reveal>
          <SpotlightCard>
            <div className="space-y-5 p-6">
              <div>
                <p className="label">jo suna gaya</p>
                <p className="hindi-tamil text-[14px] leading-relaxed text-[var(--ink)]">
                  {transcript || entry.transcript}
                </p>
              </div>
              <div className="border-t border-dashed border-[var(--line)] pt-4">
                <p className="label">khaata entry</p>
                <div className="flex flex-wrap items-baseline gap-3">
                  <span className="font-display text-2xl">{entry.customer_matched || entry.customer}</span>
                  {entry.customer_matched ? (
                    <span className="badge border border-[var(--line)] font-mono text-[var(--muted)]">khaata se mila</span>
                  ) : (
                    <span className="badge border border-[rgba(217,179,107,0.35)] font-mono text-[var(--warn)]">naya customer banega</span>
                  )}
                  <span className="badge border border-[var(--line)] font-mono">{LANG_LABEL[entry.language] || entry.language}</span>
                </div>
                <table className="mt-3 w-full text-[13px]">
                  <thead>
                    <tr className="text-left font-mono text-[10px] uppercase tracking-[0.14em] text-[var(--faint)]">
                      <th className="pb-1">cheez</th><th className="pb-1">naf</th><th className="pb-1 text-right">daam</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entry.items.map((it, i) => (
                      <tr key={i} className="border-t border-[var(--line)]">
                        <td className="py-1.5">{it.name}</td>
                        <td className="py-1.5 font-mono text-[var(--muted)]">
                          {it.qty % 1 === 0 ? it.qty.toFixed(0) : it.qty}{it.unit && ` ${it.unit}`}
                        </td>
                        <td className="py-1.5 text-right font-mono">{rupees(it.price)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t border-[var(--line)]">
                      <td className="py-2 font-display text-lg" colSpan={2}>Total</td>
                      <td className="py-2 text-right font-display text-lg">{rupees(entry.total)}</td>
                    </tr>
                  </tfoot>
                </table>
                {entry.notes && (
                  <p className="mt-1 font-mono text-[11px] text-[var(--warn)]">note: {entry.notes}</p>
                )}
              </div>
              <div className="flex gap-3">
                <button className="btn btn-primary flex-1" onClick={save} disabled={phase === "saving"}>
                  {phase === "saving" ? "darj ho raha hai…" : "khaata mein darj karein"}
                </button>
                <button
                  className="btn btn-ghost"
                  onClick={() => { setEntry(null); setTranscript(""); setPhase("idle"); }}
                  disabled={phase === "saving"}
                >
                  radd
                </button>
              </div>
            </div>
          </SpotlightCard>
        </Reveal>
      )}
    </div>
  );
}
