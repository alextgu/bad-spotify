/**
 * Sending a visitor's own clip to the agent.
 *
 * The site is static and deliberately has no backend — the 13 Aug decision was
 * that it replays a recorded run so there is nothing to host and nothing live
 * to fail. Uploading breaks that on purpose, and only locally: it talks to the
 * agent running on the same machine, which is the difference between "try it"
 * meaning *watch a recording* and meaning *watch YOUR footage*.
 *
 * So this fails often and by design — nobody browsing a deployed copy has the
 * agent running. The one thing it must never do is fail vaguely. A screen that
 * says "something went wrong" after a two-minute upload teaches people not to
 * trust the rest of it, which is exactly why the button was switched off
 * rather than wired to quietly play the sample instead.
 */

import type { Session } from "@/lib/types";

/** Where the agent might be. HTTPS first: `run.py --https` is the phone path. */
const BASES = [
  "https://127.0.0.1:8420",
  "http://127.0.0.1:8420",
];

export interface AnalyzeResult {
  session: Session;
  /** Which base answered, so the panel can say where the reasoning came from. */
  base: string;
}

export class AnalyzeError extends Error {
  constructor(message: string, readonly hint?: string) {
    super(message);
  }
}

/** Is the agent up? Cheap, and lets the button explain itself before a upload. */
export async function findAgent(): Promise<string | null> {
  for (const base of BASES) {
    try {
      const res = await fetch(`${base}/api/state`, {
        method: "GET",
        signal: AbortSignal.timeout(1500),
      });
      if (res.ok) return base;
    } catch {
      /* next */
    }
  }
  return null;
}

export async function analyze(file: File): Promise<AnalyzeResult> {
  const base = await findAgent();
  if (!base) {
    throw new AnalyzeError(
      "The agent isn't running on this machine.",
      "Start it with:  python run.py --serve     then try again.",
    );
  }

  const body = new FormData();
  body.append("file", file, file.name);

  let res: Response;
  try {
    res = await fetch(`${base}/api/analyze-video`, { method: "POST", body });
  } catch (e) {
    // The overwhelmingly likely cause, and one nobody guesses: the agent is
    // on HTTPS with a certificate this browser has never been asked to trust,
    // so the request dies before it is sent.
    throw new AnalyzeError(
      "Could not reach the agent.",
      base.startsWith("https")
        ? `Open ${base}/live once and accept the certificate, then try again.`
        : String(e),
    );
  }

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new AnalyzeError(
      `The agent refused it (${res.status}).`,
      detail.slice(0, 200),
    );
  }

  return { session: await res.json(), base };
}

/** How long is it? The marks need a real duration to land in the right place. */
export function durationOf(file: File): Promise<number> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const v = document.createElement("video");
    v.preload = "metadata";
    v.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(Number.isFinite(v.duration) ? v.duration : 0);
    };
    v.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(0);
    };
    v.src = url;
  });
}
