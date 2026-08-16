package dev.slopify.meta

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.util.concurrent.atomic.AtomicReference
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class SlopifyWearablesClientTest {
  @Test
  fun `client sends the v1 bearer and frame metadata contract`() {
    val requestHeaders = AtomicReference<Map<String, List<String>>>()
    val requestBody = AtomicReference<ByteArray>()
    val server = HttpServer.create(InetSocketAddress(0), 0)
    server.createContext("/api/wearables/v1/frames") { exchange ->
      requestHeaders.set(exchange.requestHeaders)
      requestBody.set(exchange.requestBody.readAllBytes())
      val response = """{"accepted":true,"sequence":9}""".toByteArray()
      exchange.sendResponseHeaders(200, response.size.toLong())
      exchange.responseBody.use { it.write(response) }
    }
    server.start()
    try {
      val client =
          SlopifyWearablesClient(
              backendUrl = "http://127.0.0.1:${server.address.port}",
              bearerToken = "pair-me",
          )

      val result =
          client.sendFrame(
              jpeg = byteArrayOf(0xFF.toByte(), 0xD8.toByte(), 1, 2, 0xFF.toByte(), 0xD9.toByte()),
              metadata =
                  FrameMetadata(
                      clientId = "judge-phone",
                      sessionId = "launch-a",
                      sequence = 9,
                      capturedAtMs = 1_786_802_400_123,
                      datVersion = "0.9.0",
                  ),
          )

      assertEquals(FrameResult.Accepted, result)
      val headers = requestHeaders.get().mapKeys { it.key.lowercase() }
      assertEquals(listOf("Bearer pair-me"), headers["authorization"])
      assertEquals(listOf("judge-phone"), headers["x-slopify-client-id"])
      assertEquals(listOf("launch-a"), headers["x-slopify-session-id"])
      assertEquals(listOf("9"), headers["x-slopify-sequence"])
      assertEquals(listOf("1786802400123"), headers["x-slopify-captured-at-ms"])
      assertEquals(listOf("0.9.0"), headers["x-meta-dat-version"])
      assertEquals(
          listOf(0xFF.toByte(), 0xD8.toByte(), 1, 2, 0xFF.toByte(), 0xD9.toByte()),
          requestBody.get().toList(),
      )
    } finally {
      server.stop(0)
    }
  }

  @Test
  fun `client carries retry delay from server backpressure`() {
    val server = HttpServer.create(InetSocketAddress(0), 0)
    server.createContext("/api/wearables/v1/frames") { exchange ->
      exchange.requestBody.close()
      val response =
          """{"accepted":false,"sequence":1,"reason":"busy","retry_after_ms":4500}"""
              .toByteArray()
      exchange.responseHeaders.add("Retry-After", "5")
      exchange.sendResponseHeaders(429, response.size.toLong())
      exchange.responseBody.use { it.write(response) }
    }
    server.start()
    try {
      val client =
          SlopifyWearablesClient(
              backendUrl = "http://127.0.0.1:${server.address.port}",
              bearerToken = "pair-me",
          )

      val result =
          client.sendFrame(
              byteArrayOf(1),
              FrameMetadata("judge-phone", "launch-a", 1, 1_786_802_400_123, "0.9.0"),
          )

      assertEquals(FrameResult.Busy(4_500), result)
    } finally {
      server.stop(0)
    }
  }
}
