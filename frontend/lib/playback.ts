export interface PlaybackStatus {
  backend: string | null;
  connected: boolean;
  message: string;
  account?: string | null;
  product?: string | null;
  device?: string | null;
  device_type?: string | null;
  device_active?: boolean;
}

async function detailFrom(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail || `Playback request failed (${response.status}).`;
  } catch {
    return `Playback request failed (${response.status}).`;
  }
}

export async function playbackStatus(base: string): Promise<PlaybackStatus> {
  const response = await fetch(`${base}/api/playback`, { cache: "no-store" });
  if (!response.ok) throw new Error(await detailFrom(response));
  return (await response.json()) as PlaybackStatus;
}

export async function playTrack(base: string, trackId: string): Promise<void> {
  const response = await fetch(`${base}/api/playback/play`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ track_id: trackId }),
  });
  if (!response.ok) throw new Error(await detailFrom(response));
}

export async function stopPlayback(base: string): Promise<void> {
  const response = await fetch(`${base}/api/playback/stop`, { method: "POST" });
  if (!response.ok) throw new Error(await detailFrom(response));
}
