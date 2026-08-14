"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";

/**
 * A poster frame that expands into a full player.
 *
 * The alternative — a bare <video controls> — puts browser chrome and a grey
 * rectangle at the most important point on the page. This gives us a caption
 * on the still, which is where the joke can land before anyone presses play.
 *
 * The video only mounts once opened, so an unplayed film costs nothing on
 * first load. Closing unmounts it, which also stops the audio; a modal that
 * keeps playing after you dismiss it is a genuinely annoying bug.
 */
export default function HeroVideoDialog({
  src,
  poster,
  caption,
  subcaption,
  className = "",
}: {
  src: string;
  /** Optional still. Without one, the frame is a gradient. */
  poster?: string;
  caption?: string;
  subcaption?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  // Escape to close, and don't let the page scroll behind the modal.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <>
      <motion.button
        type="button"
        onClick={() => setOpen(true)}
        aria-label={`Play${caption ? `: ${caption}` : " the film"}`}
        whileHover={{ scale: 1.012 }}
        transition={{ duration: 0.5, ease: [0.21, 0.47, 0.32, 0.98] }}
        className={`group relative block w-full overflow-hidden rounded-xl border
                    border-subtle bg-surface-1 ${className}`}
        style={{ aspectRatio: "16 / 9" }}
      >
        {poster ? (
          <img src={poster} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="h-full w-full bg-surface-1" />
        )}

        <span className="poster-vignette pointer-events-none absolute inset-0" />

        {/* The centring transform lives on the wrapper and the animation on
            the child, because `animate-ping` sets `transform: scale(2)` --
            which silently replaces the -translate-x/y and pushes the ring
            down-right of the button it's supposed to be concentric with. */}
        <span className="pointer-events-none absolute left-1/2 top-1/2 h-play w-play
                         -translate-x-1/2 -translate-y-1/2">
          <span className="absolute inset-0 rounded-full border border-white/60
                           motion-safe:animate-ping" />
          <span className="absolute inset-0 grid place-items-center rounded-full
                           bg-white/95 transition duration-interaction ease-brand
                           group-hover:bg-white">
            <svg viewBox="0 0 24 24" aria-hidden className="h-6 w-6 translate-x-px fill-plane">
              <path d="M8 5v14l11-7z" />
            </svg>
          </span>
        </span>

        {caption && (
          <span className="pointer-events-none absolute bottom-5 left-5 text-left">
            <span className="block text-lg font-semibold text-white">
              {caption}
            </span>
            {subcaption && (
              <span className="block text-sm text-white/70">{subcaption}</span>
            )}
          </span>
        )}
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onClick={() => setOpen(false)}
            role="dialog"
            aria-modal="true"
            className="fixed inset-0 z-[80] grid place-items-center bg-black/85 p-6 backdrop-blur-sm"
          >
            <button
              onClick={() => setOpen(false)}
              aria-label="Close"
              className="absolute right-7 top-6 text-2xl text-ink-muted transition duration-interaction ease-brand hover:text-white"
            >
              ✕
            </button>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.35, ease: [0.21, 0.47, 0.32, 0.98] }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-5xl overflow-hidden rounded-xl border border-subtle bg-black"
            >
              <video
                className="aspect-video w-full"
                src={src}
                controls
                autoPlay
                playsInline
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
