"""The voice. Short, deadpan, ducked over the track intro.

The quip is doing a lot of work: it is what makes this read as an agent with
an attitude rather than a shuffle button with extra steps. Keep it under ~15
words and never explain the joke.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading

from ..config import resolve_backend
from ..log import notice as print  # stdout is reserved for data


class MockNarrator:
    backend = "mock"

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}

    def say(self, text: str, duck=None) -> None:
        print(f'  [VOICE] "{text}"')


class ElevenLabsNarrator:
    backend = "elevenlabs"

    def __init__(self, cfg: dict):
        from elevenlabs.client import ElevenLabs
        self.cfg = cfg
        self.duck_to = float(cfg.get("duck_to", 0.25))
        self.max_chars = int(cfg.get("max_quip_chars", 120))
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        self.client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
        self._fallback = MockNarrator(cfg)

    def _play_bytes(self, audio: bytes) -> None:
        exe = next((e for e in ("ffplay", "mpv", "afplay") if shutil.which(e)), None)
        if not exe:
            return
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio)
            path = f.name
        args = {"ffplay": ["-nodisp", "-autoexit", "-loglevel", "quiet"],
                "mpv": ["--no-video", "--really-quiet"], "afplay": []}[exe]
        subprocess.run([exe, *args, path], check=False)

    def say(self, text: str, duck=None) -> None:
        text = text[: self.max_chars]
        prev = getattr(duck, "volume", None) if duck else None
        try:
            if duck is not None and prev is not None:
                duck.set_volume(self.duck_to)
            stream = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                model_id="eleven_flash_v2_5",   #Uses the fast narration model
                text=text,
                output_format="mp3_44100_128",
            )
            audio = b"".join(stream)
            self._play_bytes(audio)
            print(f'  [VOICE:11l] "{text}"')
        except Exception as e:
            print(f"[voice] elevenlabs failed ({e}) -> text only")
            self._fallback.say(text)
        finally:
            if duck is not None and prev is not None:
                threading.Timer(0.3, lambda: duck.set_volume(prev)).start()


def build_narrator(cfg: dict):
    backend = resolve_backend(cfg.get("backend", "mock"), "ELEVENLABS_API_KEY", "voice")
    if backend == "elevenlabs":
        try:
            return ElevenLabsNarrator(cfg)
        except Exception as e:
            print(f"[voice] elevenlabs init failed ({e}) -> mock")
    return MockNarrator(cfg)
