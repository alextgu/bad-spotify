"""The live surface: the browser's camera, or a shared screen, as the camera.

What must hold is that a posted frame goes through the SAME graph a video file
does -- gate, deadband and all. A path that quietly skipped them would look
fine in testing and behave nothing like the product on stage.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

cv2 = pytest.importorskip("cv2")
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient          # noqa: E402

from badspotify.hud.server import create_app       # noqa: E402
from badspotify.schemas import Track, Verdict, Vibe  # noqa: E402


class FakeDJState:
    def __init__(self):
        self.current = Verdict(
            track=Track(id="t1", title="Baby Shark", artist="Pinkfong", vibe=Vibe()),
            strategy="lyrical_irony", quip="Matched to the mood.")


class FakeRuntime:
    """Records what the graph was handed, so the test can check the contract."""

    class _Graph:
        def __init__(self):
            self.seen = []
            self.dj = type("DJ", (), {"state": FakeDJState()})()

        def tick(self, obs):
            self.seen.append(obs)
            from badspotify.perceive.scene import scene_from_text
            from badspotify.schemas import DJAction, DJDecision
            return {"scene": scene_from_text("a silent library during exam week"),
                    "decision": DJDecision(action=DJAction.HOLD, reason="deadband")}

    def __init__(self):
        self.graph = self._Graph()
        self.cfg = type("Cfg", (), {"get_path": lambda self, k, d=None: d})()


def jpeg(width=320, height=180) -> bytes:
    img = np.random.RandomState(1).randint(0, 255, (height, width, 3), np.uint8)
    return cv2.imencode(".jpg", img)[1].tobytes()


@pytest.fixture
def client_and_runtime():
    rt = FakeRuntime()
    return TestClient(create_app(rt)), rt


def test_the_live_page_is_served(client_and_runtime):
    client, _ = client_and_runtime
    assert client.get("/live").status_code == 200


def test_a_posted_frame_reaches_the_real_graph(client_and_runtime):
    """`graph.tick` is the whole point -- it enters at the change gate, so the
    live path gets the same bounds as everything else."""
    client, rt = client_and_runtime
    res = client.post("/api/frame", files={"file": ("f.jpg", jpeg(), "image/jpeg")})

    assert res.status_code == 200, res.text
    assert len(rt.graph.seen) == 1, "the frame never reached the graph"
    obs = rt.graph.seen[0]
    assert obs.has_frame
    assert obs.frame.ndim == 3 and obs.frame.shape[2] == 3
    assert obs.meta["source"] == "live"


def test_the_response_carries_what_the_page_renders(client_and_runtime):
    client, _ = client_and_runtime
    d = client.post("/api/frame",
                    files={"file": ("f.jpg", jpeg(), "image/jpeg")}).json()

    assert d["scene"]["setting"]
    assert d["scene"]["confidence"] is not None
    assert d["playing"]["title"] == "Baby Shark"
    assert d["action"] == "hold"


def test_a_frame_that_is_not_an_image_is_rejected_clearly(client_and_runtime):
    client, rt = client_and_runtime
    res = client.post("/api/frame",
                      files={"file": ("f.jpg", b"not a jpeg", "image/jpeg")})
    assert res.status_code == 400
    assert "decode" in res.json()["detail"]
    assert not rt.graph.seen, "garbage reached the pipeline"


def test_an_empty_frame_is_rejected(client_and_runtime):
    client, _ = client_and_runtime
    res = client.post("/api/frame", files={"file": ("f.jpg", b"", "image/jpeg")})
    assert res.status_code == 400


def test_without_a_runtime_it_says_so_rather_than_crashing():
    client = TestClient(create_app(None))
    res = client.post("/api/frame", files={"file": ("f.jpg", jpeg(), "image/jpeg")})
    assert res.status_code == 503
