/**
 * The product, rotating.
 *
 * Built out of divs and CSS 3D transforms rather than a WebGL dependency:
 * it's a few hundred bytes, it can't fail to load on stage, it stays sharp at
 * any projector resolution, and it degrades to a still frame under
 * prefers-reduced-motion.
 *
 * The camera dot on the left lens is the point of the whole object — it is the
 * only part of the hardware the agent actually needs, and the pulse marks the
 * five-second look interval.
 *
 * Geometry lives in `--rig-*` custom properties in globals.css so the pieces
 * stay in agreement when one of them moves.
 */
export default function GlassesRig({
  className = "",
}: {
  className?: string;
}) {
  return (
    <div
      className={`rig-scene ${className}`}
      role="img"
      aria-label="A pair of camera glasses, slowly rotating."
    >
      <div className="rig">
        {/* ------------------------------------------------- the front -- */}
        <div className="rig-front">
          <div className="rig-lens">
            <span className="rig-camera" />
            <span className="rig-camera-pulse" />
          </div>
          <div className="rig-bridge" />
          <div className="rig-lens" />
        </div>

        {/* --------------------------------------------------- temples -- */}
        <div className="rig-temple rig-temple-left" />
        <div className="rig-temple rig-temple-right" />
      </div>
    </div>
  );
}
