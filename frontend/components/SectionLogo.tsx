"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { brand } from "@/lib/brand";
import { VOICE_LINES } from "@/lib/audio";

/**
 * Section 2 — the mark, rippling. Click it and it talks.
 *
 * FRAMEWORK ONLY. Not designed yet.
 *
 * The brief: the DJ orb, the way a streaming service animates its own DJ —
 * a mark that pulses and ripples as if it is listening. Premium and clean
 * everywhere except the character itself, which should be *slightly derpy*.
 * The product is an idiot; the packaging is not. That contrast is the joke,
 * and it only works if exactly one of the two is silly.
 *
 * Slots this reserves:
 *
 *   [orb]      the mark. Rings ripple outward on a slow loop.
 *   [face]     where the derp lives — eyes, a tilt, whatever reads as
 *              "eager and wrong". Currently two dots as a stand-in.
 *   [caption]  one line of character, in its own voice.
 *   [creed]    the three-beat statement.
 *
 * **The audio file is deliberately missing.** The first line says the project's
 * name and we haven't picked one. Until `frontend/public/audio/intro.mp3`
 * exists, clicking shows the line as text — which reads as "not recorded yet"
 * rather than as a dead button. `scripts/voice_lines.py --render` writes it.
 *
 * Ripple animation is `.orb-*` in globals.css: pure CSS, no dependency, and it
 * stops under prefers-reduced-motion.
 */
export default function SectionLogo() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const [showText, setShowText] = useState(false);

  const line = VOICE_LINES.intro;

  useEffect(() => {
    // Don't leave it talking to an empty room if someone navigates away.
    return () => {
      audioRef.current?.pause();
    };
  }, []);

  const speak = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (speaking) {
      audio.pause();
      audio.currentTime = 0;
      setSpeaking(false);
      return;
    }

    setSpeaking(true);
    audio.currentTime = 0;
    // Missing file, unsupported codec, or a browser that refuses to autoplay:
    // all the same outcome here, and none of them should look broken.
    audio.play().catch(() => {
      setSpeaking(false);
      setShowText(true);
    });
  }, [speaking]);

  return (
    <section
      id="logo"
      className="section-page flex flex-col items-center justify-center px-6 text-center"
    >
      {/* [orb] + [face] — the whole thing is the button */}
      <button
        type="button"
        onClick={speak}
        aria-label={
          speaking ? "Stop the DJ talking" : `Hear the DJ say: ${line.text}`
        }
        className="orb-stage rounded-full transition hover:scale-[1.02]
                   focus-visible:outline focus-visible:outline-2
                   focus-visible:outline-offset-8 focus-visible:outline-scene"
      >
        <span className="orb-ripple" />
        <span className="orb-ripple orb-ripple-2" />
        <span className="orb-ripple orb-ripple-3" />
        <span className={`orb-core ${speaking ? "orb-speaking" : ""}`}>
          {/* [face] — placeholder derp. Two eyes, slightly off-centre. */}
          <span className="orb-eye orb-eye-l" />
          <span className="orb-eye orb-eye-r" />
        </span>
      </button>

      <audio
        ref={audioRef}
        src={line.file}
        preload="none"
        onEnded={() => setSpeaking(false)}
        onError={() => {
          setSpeaking(false);
          setShowText(true);
        }}
      />

      <p className="mt-8 font-mono text-xs uppercase tracking-[0.2em] text-ink-muted">
        {speaking ? "speaking" : "click it"}
      </p>

      {/* [caption] */}
      <p className="mt-8 max-w-lg text-[clamp(1.25rem,2.6vw,1.75rem)] leading-snug tracking-[-0.02em]">
        {showText ? `“${line.text}”` : "“I’ve read the room. I’m ignoring it.”"}
      </p>

      {showText && (
        <p className="mt-3 font-mono text-xs text-ink-muted">
          not recorded yet — the first line has the name in it
        </p>
      )}

      {/* [creed] */}
      <div className="mt-10 space-y-1.5">
        {brand.creed.map((l, i) => (
          <p
            key={l}
            className={`text-sm ${
              i === brand.creed.length - 1 ? "text-ink-primary" : "text-ink-muted"
            }`}
          >
            {l}
          </p>
        ))}
      </div>
    </section>
  );
}
