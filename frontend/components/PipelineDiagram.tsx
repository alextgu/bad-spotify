/**
 * The diagram judges actually read.
 *
 * Inline SVG on purpose: no dependency, no raster, and it stays sharp when
 * someone throws it on a projector at 4× or shrinks it onto a phone.
 *
 * Two things this has to communicate that a plain list of six steps cannot:
 *
 *   - the bypass. When nothing changed we skip the expensive thinking and go
 *     straight to the DJ. That dashed arc is the change gate, and it is why
 *     the loop is cheap enough to run every five seconds.
 *   - where the model calls are. Exactly two, marked. "One call, not one per
 *     field" is a decision we defend, so it should be visible, not narrated.
 *
 * Geometry: six 150-wide nodes, 44 apart, in a 1120-wide viewBox. If you add
 * a step, re-derive STEPS[].x rather than nudging numbers by hand.
 */

const NODE_W = 150;
const NODE_H = 74;
const STEP_X = 194; // NODE_W + 44 gap
const ROW_Y = 116;

type Step = {
  n: string;
  title: string;
  caption: string[];
  /** Costs a model call. Marked, because "only two" is the point. */
  model?: boolean;
};

const STEPS: Step[] = [
  { n: "01", title: "Look", caption: ["a frame, and a few", "seconds of sound"] },
  { n: "02", title: "Anything new?", caption: ["local, ~1ms,", "no model call"] },
  { n: "03", title: "Understand", caption: ["one question describes", "the whole moment"], model: true },
  { n: "04", title: "Flip it", caption: ["the opposite of", "that feeling"] },
  { n: "05", title: "Pick", caption: ["three theories of “worst”", "compete, funniest wins"], model: true },
  { n: "06", title: "Queue or cut", caption: ["line it up — or interrupt,", "if the room earned it"] },
];

const x = (i: number) => i * STEP_X;
const cx = (i: number) => x(i) + NODE_W / 2;

export default function PipelineDiagram() {
  return (
    <figure className="w-full">
      <svg
        viewBox="0 0 1120 300"
        className="h-auto w-full"
        role="img"
        aria-labelledby="pipeline-title pipeline-desc"
      >
        <title id="pipeline-title">How the loop works</title>
        <desc id="pipeline-desc">
          Six steps, repeating about every five seconds: look at the room; check
          whether anything changed; understand the moment in one model call;
          compute the opposite of it; pick the worst song from three competing
          theories in a second model call; then queue that song or cut into it.
          When nothing has changed, steps three to five are skipped and the
          decision step runs anyway on the previous read.
        </desc>

        <defs>
          <marker
            id="pipeline-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#898781" />
          </marker>
        </defs>

        {/* --- the bypass: nothing changed, skip the thinking, still decide -- */}
        <path
          d={`M ${cx(1)} ${ROW_Y} V 52 H ${cx(5)} V ${ROW_Y}`}
          fill="none"
          stroke="#2c2c2a"
          strokeWidth="1.5"
          strokeDasharray="5 5"
          markerEnd="url(#pipeline-arrow)"
        />
        <text
          x={(cx(1) + cx(5)) / 2}
          y="42"
          textAnchor="middle"
          fill="#898781"
          fontSize="13"
        >
          nothing changed — reuse the last read, and still decide
        </text>

        {STEPS.map((s, i) => (
          <g key={s.n}>
            {/* the straight run between neighbours */}
            {i > 0 && (
              <line
                x1={x(i) - 44 + 6}
                y1={ROW_Y + NODE_H / 2}
                x2={x(i) - 6}
                y2={ROW_Y + NODE_H / 2}
                stroke="#898781"
                strokeWidth="1.5"
                markerEnd="url(#pipeline-arrow)"
              />
            )}

            <rect
              x={x(i)}
              y={ROW_Y}
              width={NODE_W}
              height={NODE_H}
              rx="10"
              fill="#1a1a19"
              stroke={i === STEPS.length - 1 ? "#d95926" : "#2c2c2a"}
              strokeWidth="1.5"
            />

            <text x={x(i) + 16} y={ROW_Y + 26} fill="#898781" fontSize="11"
                  fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
              {s.n}
            </text>
            <text x={x(i) + 16} y={ROW_Y + 51} fill="#ffffff" fontSize="16"
                  fontWeight="500" letterSpacing="-0.3">
              {s.title}
            </text>

            {/* model-call marker, top-right of the node */}
            {s.model && <circle cx={x(i) + NODE_W - 16} cy={ROW_Y + 21} r="4" fill="#3987e5" />}

            {s.caption.map((line, j) => (
              <text
                key={line}
                x={x(i)}
                y={ROW_Y + NODE_H + 26 + j * 17}
                fill="#c3c2b7"
                fontSize="13"
              >
                {line}
              </text>
            ))}
          </g>
        ))}

        {/* ------------------------------------------------------- legend -- */}
        <g transform="translate(0, 268)">
          <circle cx="5" cy="-4" r="4" fill="#3987e5" />
          <text x="18" y="0" fill="#898781" fontSize="13">
            a model call — there are exactly two
          </text>

          <line x1="300" y1="-4" x2="332" y2="-4" stroke="#2c2c2a"
                strokeWidth="1.5" strokeDasharray="5 5" />
          <text x="344" y="0" fill="#898781" fontSize="13">
            skipped when the room hasn’t changed
          </text>

          <rect x="640" y="-11" width="14" height="14" rx="3" fill="none"
                stroke="#d95926" strokeWidth="1.5" />
          <text x="666" y="0" fill="#898781" fontSize="13">
            the only step that can interrupt the music
          </text>
        </g>
      </svg>
    </figure>
  );
}
