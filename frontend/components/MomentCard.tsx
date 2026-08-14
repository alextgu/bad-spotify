import { type Moment, stamp, vibeGap } from "@/lib/types";

/**
 * One decision, explained.
 *
 * Order matters here: what it saw, what it decided was the opposite, what it
 * played. That sequence is the argument -- it is what separates this from a
 * shuffle button, so keep it legible.
 */
export default function MomentCard({ moment }: { moment: Moment }) {
  const { scene, opposite, chosen, played } = moment;
  const accent = scene?.colors?.[0] ?? "#3987e5";

  return (
    <article className="rounded-xl border border-line bg-surface-1 p-5">
      <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-ink-muted">
        <span
          className="h-2.5 w-2.5 rounded-full"
          style={{ background: accent }}
        />
        {stamp(played?.at_video_time ?? moment.video_time)}
        {played?.mode && (
          <span
            className={`ml-auto rounded border px-2 py-0.5 text-[10px] ${
              played.mode === "interrupt"
                ? "border-target text-target"
                : "border-line-strong text-ink-muted"
            }`}
          >
            {played.mode === "interrupt" ? "cut in" : "queued"}
          </span>
        )}
      </div>

      <p className="mt-3 text-xs uppercase tracking-widest text-ink-muted">
        It sees
      </p>
      <p className="text-lg font-medium leading-snug">{scene?.setting}</p>
      {scene?.mood && (
        <p className="text-sm text-ink-muted">
          {scene.mood}
          {scene.confidence != null &&
            ` · ${Math.round(scene.confidence * 100)}% sure`}
        </p>
      )}

      {opposite && (
        <>
          <p className="mt-5 text-xs uppercase tracking-widest text-ink-muted">
            So it wants
          </p>
          <p className="text-sm text-ink-secondary">
            {opposite.looking_for.slice(0, 5).join(", ")}
          </p>
        </>
      )}

      {chosen && (
        <div className="mt-5 border-t border-line pt-4">
          <p className="text-xs uppercase tracking-widest text-ink-muted">
            So it plays
          </p>
          <p className="text-xl font-semibold tracking-tight">{chosen.title}</p>
          <p className="text-sm text-ink-muted">{chosen.artist}</p>
          {chosen.quip && (
            <p className="mt-3 text-base italic text-ink-secondary">
              &ldquo;{chosen.quip}&rdquo;
            </p>
          )}
          <p className="mt-3 font-mono text-xs text-ink-muted">
            via {chosen.strategy} · wrongness {vibeGap(moment).toFixed(2)}
          </p>
        </div>
      )}
    </article>
  );
}
