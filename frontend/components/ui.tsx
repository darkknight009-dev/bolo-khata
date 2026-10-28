"use client";

import { motion, useMotionValue, useSpring, useTransform } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { STATUS_STYLE } from "@/lib/api";

/* -------------------------------------------------- scroll/slide reveal --- */
export function Reveal({
  children,
  delay = 0,
  y = 14,
  className = "",
}: {
  children: React.ReactNode;
  delay?: number;
  y?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

/* ------------------------------------------- Aceternity-style spotlight --- */
export function SpotlightCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <div
      ref={ref}
      className={`card relative overflow-hidden ${className}`}
      onMouseMove={(e) => {
        const current = ref.current;
        const rect = current?.getBoundingClientRect();
        if (!current || !rect) return;
        current.style.setProperty("--mx", `${e.clientX - rect.left}px`);
        current.style.setProperty("--my", `${e.clientY - rect.top}px`);
      }}
    >
      {/* mouse-follow ember highlight — solid light, no blur/glass */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 hover-trigger"
        style={{
          background:
            "radial-gradient(340px circle at var(--mx, 50%) var(--my, 50%), rgba(228,168,83,0.08), transparent 65%)",
        }}
        ref={(el) => {
          if (!el || !ref.current) return;
          ref.current.addEventListener("mousemove", () => {
            el.style.opacity = "1";
          });
          ref.current.addEventListener("mouseleave", () => {
            el.style.opacity = "0";
          });
        }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}

/* --------------------------------------------------- animated stat number - */
export function Counter({
  value,
  format = (v: number) => `${Math.round(v)}`,
  className = "",
}: {
  value: number;
  format?: (v: number) => string;
  className?: string;
}) {
  const mv = useMotionValue(0);
  const spring = useSpring(mv, { stiffness: 90, damping: 22 });
  const text = useTransform(spring, (v) => format(v));
  const [ display, setDisplay ] = useState(format(0));

  useEffect(() => {
    mv.set(value);
  }, [value, mv]);

  useEffect(() => {
    const unsub = text.on("change", (v) => setDisplay(String(v)));
    return () => unsub();
  }, [text]);

  return <span className={className}>{display}</span>;
}

/* ------------------------------------------------------------ status dot -- */
export function StatusDot({ status }: { status: string }) {
  const pulse = status === "running" || status === "queued";
  const color =
    status === "succeeded" || status === "done"
      ? "var(--ok)"
      : status === "failed"
        ? "var(--bad)"
        : status === "running"
          ? "var(--sky)"
          : "var(--faint)";
  return (
    <span className="relative inline-flex">
      <span
        className="inline-block h-2 w-2 rounded-full"
        style={{ background: color }}
      />
      {pulse && (
        <motion.span
          className="absolute inset-0 inline-block rounded-full"
          style={{ border: `1px solid ${color}` }}
          animate={{ scale: [1, 2.1], opacity: [0.8, 0] }}
          transition={{ repeat: Infinity, duration: 1.6, ease: "easeOut" }}
        />
      )}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const per = STATUS_STYLE[status];
  const styleMap: Record<string, string> = {
    "bg-emerald-900/60 text-emerald-300": "st-ok bg-[rgba(139,191,159,0.10)]",
    "bg-rose-900/60 text-rose-300": "st-bad bg-[rgba(224,140,123,0.10)]",
    "bg-sky-900/60 text-sky-300": "st-info bg-[rgba(146,180,201,0.10)]",
  };
  const cls = styleMap[per ?? ""] ?? "text-gray-400 bg-[rgba(152,160,171,0.08)]";
  return (
    <span className={`badge relative z-10 ${cls}`}>
      <StatusDot status={status} /> {status}
    </span>
  );
}

/* ------------------------------------------------------------------- tab -- */
export function SectionHeading({
  kicker,
  title,
  children,
}: {
  kicker?: string;
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <Reveal>
      <div>
        {kicker && (
          <p className="mb-1 font-mono text-[11px] uppercase tracking-[0.22em] text-[var(--faint)]">
            {kicker}
          </p>
        )}
        <h2 className="font-display text-2xl text-[var(--ink)] sm:text-3xl">
          {title}
        </h2>
        {children}
      </div>
    </Reveal>
  );
}
