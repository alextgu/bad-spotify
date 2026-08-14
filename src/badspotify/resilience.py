"""Timeouts and retries for model calls.

`config.yaml` has always had `timeout_s` on both the perceive and judge steps.
Nothing read it, which meant a slow or hanging Gemini call would stall the whole
loop for as long as the network felt like it -- on stage, that reads as the
project being frozen.

The rule this enforces: **a late answer is worth less than a fast fallback.**
We would rather reuse the previous scene read, or drop to the chaos deck, than
stand there in silence waiting.

Note on the timeout: the underlying call keeps running in its thread after we
give up on it. We can't kill it, and that's fine -- it's a network request that
will finish and be discarded. What matters is that the loop moves on.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable, TypeVar
from .log import notice as print  # stdout is reserved for data

T = TypeVar("T")

_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="model-call")


class ModelTimeout(RuntimeError):
    """The call took longer than we're willing to wait."""


def call_with_timeout(
    fn: Callable[[], T],
    timeout_s: float,
    *,
    retries: int = 1,
    label: str = "model call",
    backoff_s: float = 0.4,
) -> T:
    """Run `fn`, giving up after `timeout_s`. Retries transient failures.

    Raises the last exception, or ModelTimeout, if every attempt fails. Callers
    are expected to catch and fall back -- see perceive/scene.py and
    agents/judge.py, which both degrade to a mock rather than propagating.
    """
    attempts = max(1, retries + 1)
    last: Exception | None = None

    for attempt in range(1, attempts + 1):
        started = time.time()
        future = _POOL.submit(fn)
        try:
            return future.result(timeout=timeout_s)
        except FuturesTimeout:
            future.cancel()
            elapsed = time.time() - started
            last = ModelTimeout(f"{label} exceeded {timeout_s:.1f}s (waited {elapsed:.1f}s)")
            print(f"[resilience] {last}"
                  + (f" -- retry {attempt}/{attempts - 1}" if attempt < attempts else ""))
        except Exception as e:
            last = e
            print(f"[resilience] {label} failed: {type(e).__name__}: {e}"
                  + (f" -- retry {attempt}/{attempts - 1}" if attempt < attempts else ""))

        if attempt < attempts:
            time.sleep(backoff_s * attempt)

    raise last if last else RuntimeError(f"{label} failed with no exception")
