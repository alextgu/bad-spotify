package dev.slopify.meta

/**
 * Keeps capture and upload strictly sequential. Slopify reasons at human-event
 * cadence, so a 24 fps camera stream would only create a queue of stale scenes.
 */
class SlopifyCaptureLoop(
    private val clientId: String,
    private val sessionId: String,
    private val datVersion: String,
    private val captureJpeg: suspend () -> ByteArray?,
    private val send: suspend (ByteArray, FrameMetadata) -> FrameResult,
    private val nowMs: () -> Long = System::currentTimeMillis,
    private val sleepMs: suspend (Long) -> Unit,
    private val intervalMs: Long = 2_000,
) {
  @Volatile private var stopped = false
  private var sequence = 0L

  val isStopped: Boolean
    get() = stopped

  fun stop() {
    stopped = true
  }

  suspend fun run(frameLimit: Int? = null) {
    stopped = false
    var frames = 0
    while (!stopped && (frameLimit == null || frames < frameLimit)) {
      val jpeg = captureJpeg()
      if (jpeg == null) {
        sleepMs(intervalMs)
        continue
      }

      sequence += 1
      frames += 1
      val result =
          send(
              jpeg,
              FrameMetadata(
                  clientId = clientId,
                  sessionId = sessionId,
                  sequence = sequence,
                  capturedAtMs = nowMs(),
                  datVersion = datVersion,
              ),
          )
      val nextDelay = if (result is FrameResult.Busy) result.retryAfterMs else intervalMs
      sleepMs(nextDelay)
    }
  }
}
