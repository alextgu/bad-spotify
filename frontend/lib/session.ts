
import type { Session } from "./types";

export const SAMPLE_SESSION_URL = "/sessions/sample.json";

export async function loadSession(url: string = SAMPLE_SESSION_URL): Promise<Session> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(
      `could not load session from ${url} (${res.status}). ` +
        `Generate one with: python run.py --video clip.mp4 --record sample`,
    );
  }
  return (await res.json()) as Session;
}


export function activeMomentIndex(
  session: Session,
  videoTime: number,
): number {
  const times = session.moments.map(
    (m) => m.played?.at_video_time ?? m.video_time ?? 0,
  );
  let idx = -1;
  for (let i = 0; i < times.length; i++) {
    if (times[i] <= videoTime) idx = i;
    else break;
  }
  return idx;
}
