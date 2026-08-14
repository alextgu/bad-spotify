import { steps } from "@/lib/brand";

/**
 * The loop, drawn.
 *
 * A row of six boxes would have been quicker and would have said nothing that
 * the six labels don't already say. The two things worth a picture are the two
 * places the line *isn't* straight:
 *
 *   - **The gate short-circuits.** If nothing changed, Notice sends it back to
 *     Look without spending a model call. That's the arc over the top, and it
 *     is the single most common path through the system on calm footage.
 *   - **Antagonize fans out.** Three strategies run at once and a judge picks
 *     between them. Drawn as three lanes rather than one box, because "three
 *     that argue" is the design and a box labelled "choose" hides it.
 *
 * Inline SVG, no dependency, no runtime. One viewBox that scales to whatever
 * width the container gives it — `SectionProduct` wraps this in `min-w-diagram`
 * and `overflow-x-auto`, so below ~700px it scrolls sideways rather than
 * shrinking the type past legibility.
 *
 * Colour follows the tokens' stated meanings, so the diagram doesn't invent a
 * third language: `scene` for the three steps that read the world as it is,
 * `target` for the two that decide what to do about it, plain ink for the one
 * that acts.
 *
 * Geometry is all derived from the constants below. If you move a node, move
 * the constant — every connector is computed from them, so nothing drifts.
 */

const NODE_W = 132;
const NODE_H = 64;
const GAP = 40;
/** The 04 -> 05 stretch is wide on purpose: the three lanes live in it. */
const FAN_GAP = 210;
const PAD = 24;

/** Spine centre. Everything vertical is measured from here. */
const MID_Y = 190;
const TOP = MID_Y - NODE_H / 2;
const BOTTOM = MID_Y + NODE_H / 2;

/** x of each node, left edge. The wide gap sits between index 3 and 4. */
const X = steps.reduce<number[]>((acc, _, i) => {
  if (i === 0) return [PAD];
  const gap = i === 4 ? FAN_GAP : GAP;
  return [...acc, acc[i - 1] + NODE_W + gap];
}, []);

const LAST = X[X.length - 1] + NODE_W;
const VIEW_W = LAST + PAD;

/** Where the gate's "nothing changed" arc peaks, and where the loop returns. */
const ARC_Y = 92;
const RETURN_Y = 272;

/* The viewBox is cropped to the marks rather than starting at 0: the arc and
   the return line are the topmost and bottommost things drawn, and anything
   above or below them is empty band that the section would have to pad around.
   Derived, not typed in, so moving ARC_Y or RETURN_Y keeps the crop honest. */
const VIEW_TOP = ARC_Y - 16;
const VIEW_BOTTOM = RETURN_Y + 16;

const centre = (i: number) => X[i] + NODE_W / 2;

/**
 * The three strategies, named as they are in the code so the diagram and
 * `music/strategies.py`'s REGISTRY can be checked against each other by eye.
 */
const LANES = [
  { name: "genre_antipode", offset: -46 },
  { name: "tempo_clash", offset: 0 },
  { name: "lyrical_irony", offset: 46 },
];

/** The colour each step is drawn in — see the note on tokens above. */
function accent(i: number) {
  if (i <= 2) return "fill-scene";
  if (i <= 4) return "fill-target";
  return "fill-ink-primary";
}

export default function PipelineDiagram() {
  const fanFrom = X[3] + NODE_W;
  const fanTo = X[4];

  return (
    <svg
      viewBox={`0 ${VIEW_TOP} ${VIEW_W} ${VIEW_BOTTOM - VIEW_TOP}`}
      className="h-auto w-full"
      role="img"
      aria-labelledby="loop-title loop-desc"
    >
      <title id="loop-title">The loop, as a diagram</title>
      <desc id="loop-desc">
        Six steps in sequence: {steps.map((s) => s.title).join(", ")}. If
        nothing has changed, step two returns to step one without calling a
        model. Between Invert and Choose, three strategies run at once —
        genre antipode, tempo clash and lyrical irony — and a judge picks one
        of them. After Commit, the loop returns to Look, about every five
        seconds.
      </desc>

      <defs>
        <marker
          id="loop-arrow"
          viewBox="0 0 8 8"
          refX="7"
          refY="4"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M0,0 L8,4 L0,8 Z" className="fill-ink-muted" />
        </marker>
      </defs>

      {/* ------------------------------------------------- the return loop --
          Drawn first so every node sits on top of it. Commit goes down, all
          the way back along the bottom, and up into Look. */}
      <path
        d={`M${centre(5)},${BOTTOM} V${RETURN_Y} H${centre(0)} V${BOTTOM}`}
        fill="none"
        className="stroke-line"
        strokeWidth="1.5"
        markerEnd="url(#loop-arrow)"
      />
      <rect
        x={VIEW_W / 2 - 74}
        y={RETURN_Y - 11}
        width="148"
        height="22"
        className="fill-plane"
      />
      <text
        x={VIEW_W / 2}
        y={RETURN_Y + 4}
        textAnchor="middle"
        className="fill-ink-muted font-mono text-[11px]"
      >
        every ~5 seconds
      </text>

      {/* ----------------------------------------------- the gate's shortcut --
          Notice back to Look, over the top. The most-travelled edge on calm
          footage, and the reason a still room costs nothing. */}
      <path
        d={`M${centre(1)},${TOP} C${centre(1)},${ARC_Y} ${centre(0)},${ARC_Y} ${centre(0)},${TOP}`}
        fill="none"
        className="stroke-line"
        strokeWidth="1.5"
        strokeDasharray="4 4"
        markerEnd="url(#loop-arrow)"
      />
      <text
        x={(centre(0) + centre(1)) / 2}
        y={ARC_Y + 2}
        textAnchor="middle"
        className="fill-ink-muted font-mono text-[11px]"
      >
        nothing changed
      </text>

      {/* ------------------------------------------------ straight connectors --
          Every gap except the wide one, which the lanes cross instead. */}
      {steps.slice(0, -1).map((s, i) =>
        i === 3 ? null : (
          <line
            key={`edge-${s.n}`}
            x1={X[i] + NODE_W}
            y1={MID_Y}
            x2={X[i + 1] - 8}
            y2={MID_Y}
            className="stroke-line"
            strokeWidth="1.5"
            markerEnd="url(#loop-arrow)"
          />
        ),
      )}

      {/* --------------------------------------------------------- the fan --
          Three lanes out of Invert, three back into Choose. The middle one is
          straight; the outer two bow away and return. */}
      <text
        x={(fanFrom + fanTo) / 2}
        y={TOP - 34}
        textAnchor="middle"
        className="fill-ink-muted font-mono text-[11px]"
      >
        three at once
      </text>

      {LANES.map((lane) => {
        const y = MID_Y + lane.offset;
        const a = fanFrom + 44;
        const b = fanTo - 44;
        return (
          <g key={lane.name}>
            <path
              d={`M${fanFrom},${MID_Y} C${fanFrom + 26},${MID_Y} ${a - 26},${y} ${a},${y} L${b},${y} C${b + 26},${y} ${fanTo - 34},${MID_Y} ${fanTo - 8},${MID_Y}`}
              fill="none"
              className="stroke-line"
              strokeWidth="1.5"
              markerEnd={lane.offset === 0 ? "url(#loop-arrow)" : undefined}
            />
            <rect
              x={(fanFrom + fanTo) / 2 - 52}
              y={y - 10}
              width="104"
              height="20"
              className="fill-plane"
            />
            <text
              x={(fanFrom + fanTo) / 2}
              y={y + 4}
              textAnchor="middle"
              className="fill-ink-muted font-mono text-[11px]"
            >
              {lane.name}
            </text>
          </g>
        );
      })}

      {/* ------------------------------------------------------- the nodes -- */}
      {steps.map((s, i) => (
        <g key={s.n}>
          <rect
            x={X[i]}
            y={TOP}
            width={NODE_W}
            height={NODE_H}
            rx="14"
            className="fill-surface-1 stroke-line"
            strokeWidth="1"
          />
          <text
            x={X[i] + 16}
            y={TOP + 24}
            className={`${accent(i)} font-mono text-[11px]`}
          >
            {s.n}
          </text>
          <text
            x={X[i] + 16}
            y={TOP + 46}
            className="fill-ink-primary text-[15px] font-medium"
          >
            {s.title}
          </text>
        </g>
      ))}
    </svg>
  );
}
