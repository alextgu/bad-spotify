"use client";

import { useEffect, useRef } from "react";
import Label from "@/components/Label";
import { samples, type Sample } from "@/lib/samples";

/**
 * The clip picker: a modal with three choices and nothing else in it.
 *
 * Modest on purpose. It is a decision the reader makes in about two seconds,
 * so it gets a dimmed ground, three cards, and no chrome — no title bar, no
 * confirm button, no second step. Clicking a card *is* the confirmation.
 *
 * The cards report the element they were clicked on (`onPick` receives the
 * card's bounding rect), which is what lets the workbench animate the chosen
 * clip out of the card it came from rather than cutting to it. Without that
 * the transition has no start position and the video has to appear from
 * nowhere.
 *
 * Keyboard and dismissal are handled properly because a modal that traps you
 * is worse than no modal: Escape closes, the backdrop closes, focus moves to
 * the first card on open and returns to whatever opened it on close.
 */
export default function ClipPicker({
  open,
  onClose,
  onPick,
}: {
  open: boolean;
  onClose: () => void;
  onPick: (sample: Sample, from: DOMRect) => void;
}) {
  const first = useRef<HTMLButtonElement>(null);
  const opener = useRef<Element | null>(null);

  useEffect(() => {
    if (!open) return;

    opener.current = document.activeElement;
    first.current?.focus();

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };

    // Capture phase: the page's ScrollController also listens for keys, and
    // arrow presses meant for this dialog must not scroll the page behind it.
    document.addEventListener("keydown", onKey, true);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      (opener.current as HTMLElement | null)?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal
      aria-label="Choose a clip"
      className="fixed inset-0 z-50 flex items-center justify-center px-gutter"
    >
      {/* The ground. Dimmed and blurred rather than blacked out, so the screen
          underneath stays recognisable and the modal reads as being in front
          of the page instead of replacing it. */}
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 cursor-default bg-ink/25 backdrop-blur-[3px]
                   motion-safe:animate-[fadeIn_400ms_cubic-bezier(0.32,0.72,0,1)_both]"
      />

      <div
        className="relative w-full max-w-content motion-safe:animate-[riseIn_520ms_cubic-bezier(0.32,0.72,0,1)_both]"
      >
        <Label tone="offset" className="block text-center">
          Choose a clip
        </Label>

        <div className="mt-rest grid gap-4 md:grid-cols-3">
          {samples.map((sample, i) => (
            <button
              key={sample.id}
              ref={i === 0 ? first : undefined}
              type="button"
              onClick={(event) =>
                onPick(sample, event.currentTarget.getBoundingClientRect())
              }
              className="group overflow-hidden rounded-card border border-hairline bg-paper text-left
                         transition-[transform,border-color] duration-interaction ease-calm
                         hover:-translate-y-1 hover:border-ink focus-visible:-translate-y-1"
            >
              <div className="relative aspect-[16/10] overflow-hidden bg-ink">
                <video
                  className="h-full w-full object-cover"
                  src={sample.src}
                  muted
                  playsInline
                  preload="metadata"
                />
                <span className="absolute bottom-3 right-3">
                  <Label className="!text-paper/70">{sample.length}</Label>
                </span>
              </div>

              <div className="p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <h3 className="font-display text-title">{sample.title}</h3>
                  {sample.placeholder && (
                    <Label className="shrink-0 !text-graphite/70">placeholder</Label>
                  )}
                </div>
                <p className="mt-1 text-caption text-graphite">{sample.blurb}</p>
              </div>
            </button>
          ))}
        </div>

        <p className="mt-rest text-center">
          <button
            type="button"
            onClick={onClose}
            className="font-mono text-label uppercase text-graphite underline decoration-hairline underline-offset-4 transition-colors duration-interaction ease-calm hover:text-ink"
          >
            Never mind
          </button>
        </p>
      </div>
    </div>
  );
}
