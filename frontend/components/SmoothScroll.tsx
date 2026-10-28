"use client";

import { ReactLenis } from "lenis/react";

export default function SmoothScroll({ children }: { children: React.ReactNode }) {
  return (
    <ReactLenis root options={{ lerp: 0.12, wheelMultiplier: 0.9, duration: 1.1 }}>
      {children}
    </ReactLenis>
  );
}
