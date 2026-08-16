package dev.slopify.meta

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import androidx.exifinterface.media.ExifInterface
import com.meta.wearable.dat.camera.Stream
import com.meta.wearable.dat.camera.types.PhotoData
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.util.UUID
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * DAT-specific edge for Meta's official CameraAccess sample at SDK 0.9.0.
 *
 * Copy this file beside the tested transport classes in an Android app that
 * already owns registration, camera permission, DeviceSession and Camera.
 * The bridge deliberately receives `Camera.stream`; it never creates a second
 * Meta session or a second Slopify decision path.
 */
class MetaDat09SlopifyBridge(
    private val stream: Stream,
    backendUrl: String,
    bearerToken: String,
    clientId: String,
) {
  private val client = SlopifyWearablesClient(backendUrl, bearerToken)
  private val loop =
      SlopifyCaptureLoop(
          clientId = clientId,
          sessionId = UUID.randomUUID().toString(),
          datVersion = "0.9.0",
          captureJpeg = { captureJpeg() },
          send = { jpeg, metadata ->
            withContext(Dispatchers.IO) { client.sendFrame(jpeg, metadata) }
          },
          sleepMs = { kotlinx.coroutines.delay(it) },
          intervalMs = 2_000,
      )
  private var job: Job? = null
  private var pendingStartScope: CoroutineScope? = null
  private val lifecycleLock = Any()

  fun start(scope: CoroutineScope) {
    synchronized(lifecycleLock) {
      if (job?.isActive == true) return
      // A cancelled HttpURLConnection may remain in blocking IO until its
      // timeout. Remember one requested restart, then launch it only after the
      // old job has really completed so uploads can never overlap.
      if (job?.isCompleted == false) {
        pendingStartScope = scope
        return
      }
      launchLocked(scope)
    }
  }

  fun stop() {
    synchronized(lifecycleLock) {
      pendingStartScope = null
      loop.stop()
      job?.cancel()
      // Completion clears the reference. Keeping it here prevents start()
      // from overlapping a blocking request that has not stopped yet.
    }
  }

  /** Caller holds [lifecycleLock]. */
  private fun launchLocked(scope: CoroutineScope) {
    val launched = scope.launch { loop.run() }
    job = launched
    launched.invokeOnCompletion {
      synchronized(lifecycleLock) {
        if (job !== launched) return@synchronized
        job = null
        pendingStartScope?.let { pending ->
          pendingStartScope = null
          launchLocked(pending)
        }
      }
    }
  }

  private suspend fun captureJpeg(): ByteArray? {
    var jpeg: ByteArray? = null
    stream
        .capturePhoto()
        .onSuccess { photo -> jpeg = photo.toJpeg() }
        .onFailure { _, _ -> jpeg = null }
    return jpeg
  }

  private fun PhotoData.toJpeg(): ByteArray? {
    val bitmap =
        when (this) {
          is PhotoData.Bitmap -> bitmap
          is PhotoData.HEIC -> decodeHeic(data)
        } ?: return null
    return ByteArrayOutputStream().use { output ->
      if (!bitmap.compress(Bitmap.CompressFormat.JPEG, 88, output)) return null
      output.toByteArray()
    }
  }

  private fun decodeHeic(data: ByteBuffer): Bitmap? {
    val copy = data.duplicate().apply { rewind() }
    val bytes = ByteArray(copy.remaining())
    copy.get(bytes)
    val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: return null
    val exif = ExifInterface(ByteArrayInputStream(bytes))
    val orientation =
        exif.getAttributeInt(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_NORMAL,
        )
    val matrix = Matrix()
    when (orientation) {
      ExifInterface.ORIENTATION_ROTATE_90 -> matrix.postRotate(90f)
      ExifInterface.ORIENTATION_ROTATE_180 -> matrix.postRotate(180f)
      ExifInterface.ORIENTATION_ROTATE_270 -> matrix.postRotate(270f)
      ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> matrix.preScale(-1f, 1f)
      ExifInterface.ORIENTATION_FLIP_VERTICAL -> matrix.preScale(1f, -1f)
      ExifInterface.ORIENTATION_TRANSPOSE -> {
        matrix.preScale(-1f, 1f)
        matrix.postRotate(270f)
      }
      ExifInterface.ORIENTATION_TRANSVERSE -> {
        matrix.preScale(-1f, 1f)
        matrix.postRotate(90f)
      }
    }
    if (matrix.isIdentity) return bitmap
    return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
        .also { if (it !== bitmap) bitmap.recycle() }
  }
}
