package dev.slopify.meta

import java.net.HttpURLConnection
import java.net.URL

data class FrameMetadata(
    val clientId: String,
    val sessionId: String,
    val sequence: Long,
    val capturedAtMs: Long,
    val datVersion: String,
)

sealed interface FrameResult {
  data object Accepted : FrameResult

  data class Busy(val retryAfterMs: Long) : FrameResult

  data class Skipped(val reason: String) : FrameResult

  data object Unauthorized : FrameResult

  data class Failure(val status: Int, val message: String) : FrameResult
}

/** Small dependency-free client for Slopify's Wearables API v1. */
class SlopifyWearablesClient(
    backendUrl: String,
    private val bearerToken: String,
    private val connectTimeoutMs: Int = 3_000,
    private val readTimeoutMs: Int = 15_000,
) {
  private val frameUrl = URL(backendUrl.trimEnd('/') + "/api/wearables/v1/frames")

  fun sendFrame(jpeg: ByteArray, metadata: FrameMetadata): FrameResult {
    val connection = frameUrl.openConnection() as HttpURLConnection
    return try {
      connection.requestMethod = "POST"
      connection.doOutput = true
      connection.connectTimeout = connectTimeoutMs
      connection.readTimeout = readTimeoutMs
      connection.setRequestProperty("Authorization", "Bearer $bearerToken")
      connection.setRequestProperty("X-Slopify-Client-Id", metadata.clientId)
      connection.setRequestProperty("X-Slopify-Session-Id", metadata.sessionId)
      connection.setRequestProperty("X-Slopify-Sequence", metadata.sequence.toString())
      connection.setRequestProperty("X-Slopify-Captured-At-Ms", metadata.capturedAtMs.toString())
      connection.setRequestProperty("X-Meta-Dat-Version", metadata.datVersion)
      connection.setRequestProperty("Content-Type", "image/jpeg")
      connection.setFixedLengthStreamingMode(jpeg.size)

      connection.outputStream.use { output ->
        output.write(jpeg)
      }

      val status = connection.responseCode
      val stream = if (status in 200..299) connection.inputStream else connection.errorStream
      val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
      when {
        status == 429 -> FrameResult.Busy(retryDelayMs(connection, body))
        status == 401 -> FrameResult.Unauthorized
        status in 200..299 && body.contains("\"accepted\":true") -> FrameResult.Accepted
        status in 200..299 -> FrameResult.Skipped(jsonString(body, "reason") ?: "not_accepted")
        else -> FrameResult.Failure(status, body)
      }
    } catch (error: Exception) {
      FrameResult.Failure(0, error.message ?: error::class.java.simpleName)
    } finally {
      connection.disconnect()
    }
  }

  private fun retryDelayMs(connection: HttpURLConnection, body: String): Long {
    val fromBody = Regex("\"retry_after_ms\"\\s*:\\s*(\\d+)").find(body)
    if (fromBody != null) return fromBody.groupValues[1].toLong()
    return (connection.getHeaderField("Retry-After")?.toLongOrNull() ?: 2L) * 1_000
  }

  private fun jsonString(body: String, key: String): String? =
      Regex("\"${Regex.escape(key)}\"\\s*:\\s*\"([^\"]+)\"")
          .find(body)
          ?.groupValues
          ?.get(1)
}
