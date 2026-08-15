"""
Feasibility test: "speed" from video via optical flow magnitude.

Farneback dense optical flow gives a per-pixel (dx, dy) displacement
between consecutive frames. Averaging the magnitude of that field is a
direct, literal measure of "how much is moving, how fast" -- this is a
cleaner and more semantically honest signal than blur-variance (which
conflates motion blur with plain out-of-focus blur), so I'd use this as
the primary speed signal and treat blur-variance as an optional cheap
fallback if optical flow is too slow for your loop budget.

Ground truth: a slow-moving square vs a fast-moving square, same frame
size and duration, should produce clearly separated average flow
magnitudes.
"""

import numpy as np
import cv2


def make_moving_square_video(pixels_per_frame: float, n_frames=15, size=200, sq=30):
    """A white square moving horizontally at a fixed speed (px/frame)."""
    frames = []
    x = 10
    for i in range(n_frames):
        frame = np.zeros((size, size), dtype=np.uint8)
        cx = int(x + i * pixels_per_frame) % (size - sq)
        frame[50:50+sq, cx:cx+sq] = 255
        frames.append(frame)
    return frames


def avg_optical_flow_magnitude(frames) -> float:
    mags = []
    for i in range(len(frames) - 1):
        flow = cv2.calcOpticalFlowFarneback(
            frames[i], frames[i+1], None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
        )
        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mags.append(mag.mean())
    return float(np.mean(mags))


if __name__ == "__main__":
    slow = make_moving_square_video(pixels_per_frame=1.0)
    fast = make_moving_square_video(pixels_per_frame=12.0)

    slow_speed = avg_optical_flow_magnitude(slow)
    fast_speed = avg_optical_flow_magnitude(fast)

    print(f"slow square (1 px/frame):  avg flow magnitude = {slow_speed:.3f}")
    print(f"fast square (12 px/frame): avg flow magnitude = {fast_speed:.3f}")
    print(f"separation ratio: {fast_speed / (slow_speed + 1e-6):.1f}x")
