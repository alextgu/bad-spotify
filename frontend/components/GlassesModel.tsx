"use client";

import { Component, Suspense, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { Bounds, Center, OrbitControls, useGLTF } from "@react-three/drei";
import GlassesRig from "@/components/GlassesRig";

/**
 * The real glasses: a glTF model, orbitable with the mouse.
 *
 * ---------------------------------------------------------------------------
 * It falls back, and that is the important part
 * ---------------------------------------------------------------------------
 * This is 1.5MB of model plus three.js on a page whose first rule is that
 * nothing may fail live. WebGL can be unavailable, the file can 404, a driver
 * on a borrowed projector laptop can refuse — and the answer to all three is
 * the same: drop to `GlassesRig`, the CSS-and-divs pair that was here before.
 * It is a few hundred bytes and it cannot fail. A section that renders nothing
 * because a model did not load is worse than one that renders the cheap
 * version.
 *
 * So: an error boundary around the canvas for load and context failures, and
 * `Suspense` with the same fallback for the seconds before the model arrives.
 *
 * ---------------------------------------------------------------------------
 * Credit
 * ---------------------------------------------------------------------------
 * Model by **mminharali** on Sketchfab. The credit is rendered on the page as
 * well as written here — an attribution that only exists in a source comment
 * is not an attribution.
 *
 * The archive shipped without a licence file. Sketchfab models are usually
 * CC-BY, which requires exactly this credit, but nobody has checked the
 * listing. Worth confirming before this page is public, along with the
 * separate question of Ray-Ban Meta's trademarked product design.
 */

const MODEL = "/models/glasses.glb";

function Model() {
  const { scene } = useGLTF(MODEL);
  return <primitive object={scene} />;
}

/**
 * Class component because React error boundaries have no hook equivalent —
 * `componentDidCatch` is still the only way to catch a render-time throw from
 * a child, which is exactly how a failed GLTF load surfaces.
 */
class Fallback extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) return <GlassesRig />;
    return this.props.children;
  }
}

export default function GlassesModel({ className = "" }: { className?: string }) {
  return (
    <div className={`relative h-[clamp(320px,42vh,460px)] w-full ${className}`}>
      <Fallback>
        <Canvas
          camera={{ position: [0, 0.1, 3.4], fov: 38 }}
          dpr={[1, 2]}
          // `alpha` so the paper ground and the line grid show through rather
          // than the model sitting on its own black rectangle.
          gl={{ alpha: true, antialias: true }}
          className="!touch-none"
        >
          {/* Three lights, no HDR environment: an environment map means either
              an external CDN request or another megabyte of asset, and this
              object is matte plastic and glass that does not need one. */}
          <ambientLight intensity={0.9} />
          <directionalLight position={[3, 4, 5]} intensity={2.1} />
          <directionalLight position={[-4, -1, -3]} intensity={0.7} />

          {/* `Bounds fit` measures the model and frames the camera to it, and
              `Center` puts its origin at the middle. That replaces a hardcoded
              scale and offset, which were a guess: the export's native size is
              whatever Blender wrote, and a magic number that happens to look
              right for this file breaks the moment the file is replaced.
              `observe` re-fits on resize, so it also holds up when the column
              changes width. */}
          <Suspense fallback={null}>
            <Bounds fit clip observe margin={1.15}>
              <Center>
                <Model />
              </Center>
            </Bounds>
          </Suspense>

          {/* Drag to turn, and nothing else. Zoom and pan are off because this
              is an object on a page, not a viewer — letting someone dolly into
              the inside of a temple arm is a way to get lost, not a feature. */}
          <OrbitControls
            makeDefault
            enableZoom={false}
            enablePan={false}
            autoRotate
            autoRotateSpeed={0.9}
            // Keeps it roughly eye-level: you can spin it all the way round
            // but not tip it onto its back.
            minPolarAngle={Math.PI / 2.6}
            maxPolarAngle={Math.PI / 1.7}
          />
        </Canvas>
      </Fallback>
    </div>
  );
}

useGLTF.preload(MODEL);
