/** Microphone -> 16 kHz mono 16-bit WAV, captured in the browser (no server conversion). */

const WORKLET_SRC = `
class PcmCollector extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.targetRate = (options && options.processorOptions && options.processorOptions.targetRate) || 16000;
    this.buffers = [];
    this.port.onmessage = () => this.finalize(); // main thread asks us to stop
    this._flushPortion();
  }
  _flushPortion() {
    // chunk of 100 ms of source-rate samples between postMessage calls
    this.portion = [];
    this.portionTarget = Math.round(sampleRate * 0.1);
  }
  process(inputs) {
    const input = inputs[0];
    if (input && input[0]) this.push(input[0]);
    return true; // keep alive until stopped
  }
  push(samples) {
    this.portion.push(...samples);
    if (this.portion.length >= this.portionTarget) {
      this.buffers.push(Float32Array.from(this.portion));
      this.portion = [];
    }
  }
  finalize() {
    if (this.portion.length) this.buffers.push(Float32Array.from(this.portion));
    const down = downsample(concat(this.buffers), sampleRate, this.targetRate);
    this.port.postMessage(down, [down.buffer]);
    return false; // stop
  }
}
function concat(parts) {
  let n = 0;
  for (const p of parts) n += p.length;
  const out = new Float32Array(n);
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}
function downsample(src, srcRate, dstRate) {
  if (dstRate >= srcRate) return src;
  const ratio = srcRate / dstRate;
  const n = Math.floor(src.length / ratio);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const start = Math.floor(i * ratio);
    const end = Math.min(src.length, Math.floor((i + 1) * ratio));
    let sum = 0;
    for (let j = start; j < end; j++) sum += src[j];
    out[i] = end > start ? sum / (end - start) : 0;
  }
  return out;
}
registerProcessor("pcm-collector", PcmCollector);
`;

function encodeWav(samples: Float32Array, rate: number): ArrayBuffer {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeStr = (off: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i));
  };
  writeStr(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeStr(36, "data");
  view.setUint32(40, samples.length * 2, true);
  let off = 44;
  for (let i = 0; i < samples.length; i++, off += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

export type Recorder = {
  stop: () => Promise<Blob>; // resolves with a 16 kHz mono WAV blob
};

export async function startRecording(): Promise<Recorder> {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
  const ctx = new AudioContext();
  const source = ctx.createMediaStreamSource(stream);
  const workletUrl = URL.createObjectURL(
    new Blob([WORKLET_SRC], { type: "application/javascript" })
  );
  await ctx.audioWorklet.addModule(workletUrl);
  const node = new AudioWorkletNode(ctx, "pcm-collector", {
    processorOptions: { targetRate: 16000 },
  });
  source.connect(node);

  return {
    stop: () =>
      new Promise<Blob>((resolve) => {
        node.port.onmessage = (event: MessageEvent) => {
          const samples = new Float32Array(event.data);
          source.disconnect();
          node.disconnect();
          stream.getTracks().forEach((t) => t.stop());
          ctx.close();
          URL.revokeObjectURL(workletUrl);
          resolve(new Blob([encodeWav(samples, 16000)], { type: "audio/wav" }));
        };
        node.port.postMessage({ type: "finalize" });
        // the processor's finalize() posts the samples back
      }),
  };
}

export function blobToB64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result);
      resolve(dataUrl.slice(dataUrl.indexOf(",") + 1));
    };
    reader.onerror = () => reject(new Error("could not read audio blob"));
    reader.readAsDataURL(blob);
  });
}
