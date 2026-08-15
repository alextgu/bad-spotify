import type { Shot } from "@/lib/site";

/**
 * A photograph or film that hasn't been shot yet.
 *
 * It prints the filename it is waiting for and the art direction for it, so
 * the page is its own shoot list. Drop the file into `public/`, replace this
 * with an <img> or <video>, delete nothing else.
 *
 * Deliberately plainer than the real footage will be — see the note on `.slot`
 * in globals.css.
 */
export default function Slot({
  shot,
  className = "",
}: {
  shot: Shot;
  className?: string;
}) {
  return (
    <div className={`slot ${className}`} data-shot={shot.file} aria-hidden>
      <span>
        <b>{shot.file}</b>
        {shot.note.map((line) => (
          <span key={line} className="block">
            {line}
          </span>
        ))}
      </span>
    </div>
  );
}
