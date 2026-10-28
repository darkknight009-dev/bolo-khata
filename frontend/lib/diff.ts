// Mirrors backend/wer.py policy: punctuation-tolerant, case-folding whitespace
// tokenisation. Returns tokens for reference with an aligned hypothesis word so
// the UI can highlight what the bot misheard.
export type DiffToken = { word: string; status: "ok" | "sub" | "missing" };

function tokenize(text: string): string[] {
  if (!text) return [];
  const norm = text.normalize("NFC").toLowerCase();
  const stripped = norm.replace(/[।|,.;:?!—–"'“”‘’()\[\]{}…-]/g, " ");
  return stripped.split(/\s+/).filter(Boolean);
}

export function wordDiff(ref: string, hyp: string): DiffToken[] {
  const refW = tokenize(ref);
  const hypW = tokenize(hyp);
  const nR = refW.length;
  const nH = hypW.length;
  const dp: number[][] = Array.from({ length: nR + 1 }, () =>
    new Array(nH + 1).fill(0)
  );
  for (let i = 0; i <= nR; i++) dp[i][0] = i;
  for (let j = 0; j <= nH; j++) dp[0][j] = j;
  for (let i = 1; i <= nR; i++)
    for (let j = 1; j <= nH; j++)
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + (refW[i - 1] === hypW[j - 1] ? 0 : 1)
      );

  const out: DiffToken[] = [];
  let i = nR;
  let j = nH;
  while (i > 0 || j > 0) {
    if (
      i > 0 &&
      j > 0 &&
      refW[i - 1] === hypW[j - 1] &&
      dp[i][j] === dp[i - 1][j - 1]
    ) {
      out.push({ word: refW[i - 1], status: "ok" });
      i--;
      j--;
    } else if (
      i > 0 &&
      j > 0 &&
      dp[i][j] === dp[i - 1][j - 1] + 1
    ) {
      out.push({ word: hypW[j - 1] || "", status: "sub" });
      i--;
      j--;
    } else if (i > 0 && dp[i][j] === dp[i - 1][j] + 1) {
      out.push({ word: refW[i - 1], status: "missing" });
      i--;
    } else {
      j--;
    }
  }
  out.reverse();
  return out;
}
