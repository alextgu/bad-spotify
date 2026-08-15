/**
 * Where the pictures and films actually live.
 *
 * The deadline problem this solves: the footage will not exist until after the
 * code is frozen. So every slot on the page reads its source from
 * `public/media.json` at RUNTIME rather than at build time. Swapping a
 * placeholder for a real YouTube link is then a one-line edit to a data file
 * that ships next to the site, with no component touched and no rebuild.
 *
 * Fetched once and shared. A failed fetch is not an error: every slot falls
 * back to the placeholder it already shows, which is the correct behaviour
 * both before the footage exists and if the file is ever malformed.
 */

export interface MediaEntry {
  url: string;
  /** Background slots want this. A film someone chooses to watch does not. */
  autoplay?: boolean;
  loop?: boolean;
  /** Poster frame for a file-backed video. */
  poster?: string;
}

export type MediaValue = string | MediaEntry;

let cache: Promise<Record<string, MediaValue>> | null = null;

export function loadMedia(): Promise<Record<string, MediaValue>> {
  if (!cache) {
    cache = fetch("/media.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : {}))
      .catch(() => ({}));
  }
  return cache;
}

export function entryFor(
  map: Record<string, MediaValue>,
  key: string,
): MediaEntry | null {
  const raw = map?.[key];
  if (!raw) return null;
  const entry = typeof raw === "string" ? { url: raw } : raw;
  return entry.url?.trim() ? entry : null;
}

/**
 * The YouTube id out of any shape of link people actually paste.
 *
 * Covers watch?v=, youtu.be/, /shorts/ and /embed/, because whoever swaps the
 * link at 3am will paste whatever the address bar gave them, and a link that
 * silently does not play is worse than no link at all.
 */
export function youTubeId(url: string): string | null {
  const patterns = [
    /[?&]v=([\w-]{6,})/,
    /youtu\.be\/([\w-]{6,})/,
    /youtube\.com\/shorts\/([\w-]{6,})/,
    /youtube\.com\/embed\/([\w-]{6,})/,
  ];
  for (const p of patterns) {
    const m = url.match(p);
    if (m) return m[1];
  }
  return null;
}

export function youTubeEmbed(
  id: string,
  { autoplay = false, loop = false }: { autoplay?: boolean; loop?: boolean },
): string {
  const q = new URLSearchParams({
    rel: "0",
    modestbranding: "1",
    playsinline: "1",
  });
  if (autoplay) {
    q.set("autoplay", "1");
    // Browsers refuse to autoplay with sound. Muting is the only way an
    // autoplaying background film starts at all.
    q.set("mute", "1");
  }
  if (loop) {
    q.set("loop", "1");
    q.set("playlist", id); // YouTube needs this for a single-video loop
  }
  return `https://www.youtube.com/embed/${id}?${q.toString()}`;
}

export function isImage(url: string): boolean {
  return /\.(png|jpe?g|gif|webp|avif)(\?|$)/i.test(url);
}
