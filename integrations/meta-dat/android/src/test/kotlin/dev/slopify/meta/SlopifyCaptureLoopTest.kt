package dev.slopify.meta

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runTest

class SlopifyCaptureLoopTest {
  @Test
  fun `frames are ordered and never overlap`() = runTest {
    var capture = 0
    var sending = false
    var overlap = false
    val seen = mutableListOf<Long>()
    val sessions = mutableListOf<String>()
    val loop =
        SlopifyCaptureLoop(
            clientId = "judge-phone",
            sessionId = "launch-a",
            datVersion = "0.9.0",
            captureJpeg = { byteArrayOf((++capture).toByte()) },
            send = { _, metadata ->
              if (sending) overlap = true
              sending = true
              seen += metadata.sequence
              sessions += metadata.sessionId
              sending = false
              FrameResult.Accepted
            },
            nowMs = { 1_786_802_400_000 },
            sleepMs = {},
            intervalMs = 2_000,
        )

    loop.run(frameLimit = 3)

    assertEquals(listOf(1L, 2L, 3L), seen)
    assertEquals(listOf("launch-a", "launch-a", "launch-a"), sessions)
    assertFalse(overlap)
  }

  @Test
  fun `server backpressure controls the next capture delay`() = runTest {
    val delays = mutableListOf<Long>()
    val results = ArrayDeque<FrameResult>().apply {
      add(FrameResult.Busy(retryAfterMs = 4_500))
      add(FrameResult.Accepted)
    }
    val loop =
        SlopifyCaptureLoop(
            clientId = "judge-phone",
            sessionId = "launch-a",
            datVersion = "0.9.0",
            captureJpeg = { byteArrayOf(1) },
            send = { _, _ -> results.removeFirst() },
            nowMs = { 1_786_802_400_000 },
            sleepMs = { delays += it },
            intervalMs = 2_000,
        )

    loop.run(frameLimit = 2)

    assertEquals(listOf(4_500L, 2_000L), delays)
  }

  @Test
  fun `stop prevents another capture after an in flight request`() = runTest {
    val entered = CompletableDeferred<Unit>()
    val release = CompletableDeferred<Unit>()
    var captures = 0
    lateinit var loop: SlopifyCaptureLoop
    loop =
        SlopifyCaptureLoop(
            clientId = "judge-phone",
            sessionId = "launch-a",
            datVersion = "0.9.0",
            captureJpeg = { byteArrayOf((++captures).toByte()) },
            send = { _, _ ->
              entered.complete(Unit)
              release.await()
              FrameResult.Accepted
            },
            nowMs = { 1_786_802_400_000 },
            sleepMs = {},
            intervalMs = 2_000,
        )

    val running = async { loop.run() }
    entered.await()
    loop.stop()
    release.complete(Unit)
    running.await()

    assertEquals(1, captures)
    assertTrue(loop.isStopped)
  }
}
