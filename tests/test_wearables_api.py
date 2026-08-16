"""Meta companion transport into the same live graph used by every camera."""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

cv2 = pytest.importorskip("cv2")
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from badspotify.hud.server import create_app  # noqa: E402
from badspotify.schemas import Track, Verdict, Vibe  # noqa: E402


class FakeConfig:
    def __init__(self, values: dict | None = None):
        self.values = values or {}

    def get_path(self, key: str, default=None):
        return self.values.get(key, default)


class FakeRuntime:
    class Graph:
        def __init__(self):
            self.seen = []
            self.entered = threading.Event()
            self.release = threading.Event()
            self.block = False
            self.dj = type(
                "DJ",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "current": Verdict(
                                track=Track(
                                    id="t1",
                                    title="Baby Shark",
                                    artist="Pinkfong",
                                    vibe=Vibe(),
                                ),
                                strategy="lyrical_irony",
                                quip="Matched to the mood.",
                            )
                        },
                    )()
                },
            )()

        def tick(self, obs):
            self.seen.append(obs)
            self.entered.set()
            if self.block:
                assert self.release.wait(3), "test did not release blocked graph"
            from badspotify.perceive.scene import scene_from_text
            from badspotify.schemas import DJAction, DJDecision

            return {
                "scene": scene_from_text("a silent library during exam week"),
                "decision": DJDecision(action=DJAction.HOLD, reason="deadband"),
                "verdict": self.dj.state.current,
                "play_error": None,
            }

    def __init__(self, values: dict | None = None):
        self.cfg = FakeConfig(values)
        self.graph = self.Graph()


def jpeg(width: int = 320, height: int = 180) -> bytes:
    image = np.random.RandomState(7).randint(0, 255, (height, width, 3), np.uint8)
    return cv2.imencode(".jpg", image)[1].tobytes()


def frame_headers(sequence: int = 1, token: str = "pair-me") -> dict[str, str]:
    return {
        "Content-Type": "image/jpeg",
        "Authorization": f"Bearer {token}",
        "X-Slopify-Client-Id": "judge-phone",
        "X-Slopify-Session-Id": "launch-a",
        "X-Slopify-Sequence": str(sequence),
        "X-Slopify-Captured-At-Ms": "1786802400123",
        "X-Meta-Dat-Version": "0.9.0",
    }


@pytest.fixture
def client_and_runtime(monkeypatch):
    monkeypatch.setenv("SLOPIFY_WEARABLE_TOKEN", "pair-me")
    runtime = FakeRuntime()
    return TestClient(create_app(runtime)), runtime


def post_frame(client: TestClient, sequence: int = 1, token: str = "pair-me"):
    return client.post(
        "/api/wearables/v1/frames",
        headers=frame_headers(sequence, token),
        content=jpeg(),
    )


def test_capabilities_describe_the_companion_contract(client_and_runtime):
    client, _ = client_and_runtime

    response = client.get("/api/wearables/v1/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "service": "slopify",
        "protocol_version": 1,
        "ready": True,
        "frame_endpoint": "/api/wearables/v1/frames",
        "accepted_content_types": ["image/jpeg"],
        "max_frame_bytes": 5 * 1024 * 1024,
        "max_frame_pixels": 12_000_000,
        "min_interval_ms": 2000,
        "authentication": "bearer",
    }


def test_meta_frame_enters_the_real_graph_with_device_metadata(client_and_runtime):
    client, runtime = client_and_runtime

    response = post_frame(client, sequence=7)

    assert response.status_code == 200, response.text
    assert response.json()["accepted"] is True
    assert response.json()["sequence"] == 7
    assert response.json()["chosen"]["title"] == "Baby Shark"
    assert len(runtime.graph.seen) == 1
    observation = runtime.graph.seen[0]
    assert observation.has_frame
    assert observation.ts == pytest.approx(1786802400.123)
    assert observation.meta == {
        "source": "meta_glasses",
        "client_id": "judge-phone",
        "session_id": "launch-a",
        "sequence": 7,
        "captured_at_ms": 1786802400123,
        "meta_dat_version": "0.9.0",
    }


@pytest.mark.parametrize("headers", [{}, frame_headers(token="wrong")])
def test_lan_frame_rejects_missing_or_wrong_token_without_running_graph(
    client_and_runtime, headers
):
    client, runtime = client_and_runtime

    response = client.post(
        "/api/wearables/v1/frames",
        headers=headers,
        content=jpeg(),
    )

    assert response.status_code == 401
    assert runtime.graph.seen == []


def test_duplicate_or_older_frame_is_acknowledged_without_reprocessing(client_and_runtime):
    client, runtime = client_and_runtime
    assert post_frame(client, sequence=4).status_code == 200

    duplicate = post_frame(client, sequence=4)
    older = post_frame(client, sequence=3)

    assert duplicate.status_code == 200
    assert duplicate.json() == {"accepted": False, "sequence": 4, "reason": "duplicate"}
    assert older.status_code == 200
    assert older.json() == {"accepted": False, "sequence": 3, "reason": "out_of_order"}
    assert len(runtime.graph.seen) == 1


def test_new_companion_session_can_restart_its_sequence(client_and_runtime):
    client, runtime = client_and_runtime
    assert post_frame(client, sequence=4).status_code == 200
    restarted = frame_headers(sequence=1)
    restarted["X-Slopify-Session-Id"] = "launch-b"

    response = client.post(
        "/api/wearables/v1/frames",
        headers=restarted,
        content=jpeg(),
    )

    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert len(runtime.graph.seen) == 2


def test_capabilities_are_readable_from_a_statically_hosted_launch_page(
    client_and_runtime,
):
    client, _ = client_and_runtime

    response = client.get(
        "/api/wearables/v1/capabilities",
        headers={"Origin": "https://slopify.example"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_invalid_image_is_rejected_before_the_graph(client_and_runtime):
    client, runtime = client_and_runtime

    response = client.post(
        "/api/wearables/v1/frames",
        headers=frame_headers(),
        content=b"not an image",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "could not decode that frame"
    assert runtime.graph.seen == []


def test_pixel_limit_is_checked_before_opencv_decode(monkeypatch):
    monkeypatch.setenv("SLOPIFY_WEARABLE_TOKEN", "pair-me")
    runtime = FakeRuntime({"wearables.max_frame_pixels": 100})
    client = TestClient(create_app(runtime))

    response = post_frame(client)

    assert response.status_code == 413
    assert response.json()["detail"] == "frame dimensions are too large"
    assert runtime.graph.seen == []


def test_raw_body_is_streamed_only_up_to_the_byte_limit(monkeypatch):
    monkeypatch.setenv("SLOPIFY_WEARABLE_TOKEN", "pair-me")
    runtime = FakeRuntime({"wearables.max_frame_bytes": 10})
    client = TestClient(create_app(runtime))

    response = post_frame(client)

    assert response.status_code == 413
    assert response.json()["detail"] == "frame is too large"
    assert runtime.graph.seen == []


def test_second_frame_gets_backpressure_while_graph_is_busy(client_and_runtime):
    client, runtime = client_and_runtime
    runtime.graph.block = True
    first_response = []

    first = threading.Thread(target=lambda: first_response.append(post_frame(client, sequence=1)))
    first.start()
    assert runtime.graph.entered.wait(2), "first frame never entered the graph"

    second = post_frame(client, sequence=2)
    runtime.graph.release.set()
    first.join(timeout=3)

    assert second.status_code == 429
    assert second.headers["retry-after"] == "2"
    assert second.json() == {
        "accepted": False,
        "sequence": 2,
        "reason": "busy",
        "retry_after_ms": 2000,
    }
    assert len(first_response) == 1 and first_response[0].status_code == 200
    assert len(runtime.graph.seen) == 1


def test_loopback_development_can_run_without_a_shared_token(monkeypatch):
    monkeypatch.delenv("SLOPIFY_WEARABLE_TOKEN", raising=False)
    runtime = FakeRuntime({"hud.host": "127.0.0.1"})
    client = TestClient(create_app(runtime))

    capabilities = client.get("/api/wearables/v1/capabilities").json()
    response = client.post(
        "/api/wearables/v1/frames",
        headers={key: value for key, value in frame_headers().items() if key != "Authorization"},
        content=jpeg(),
    )

    assert capabilities["authentication"] == "none"
    assert response.status_code == 200


def test_lan_wearables_api_stays_closed_without_a_token(monkeypatch):
    monkeypatch.delenv("SLOPIFY_WEARABLE_TOKEN", raising=False)
    runtime = FakeRuntime({"hud.host": "0.0.0.0"})
    client = TestClient(create_app(runtime))

    capabilities = client.get("/api/wearables/v1/capabilities")
    response = client.post(
        "/api/wearables/v1/frames",
        headers={key: value for key, value in frame_headers().items() if key != "Authorization"},
        content=jpeg(),
    )

    assert capabilities.json()["ready"] is False
    assert response.status_code == 503
    assert "SLOPIFY_WEARABLE_TOKEN" in response.json()["detail"]
