# Meta glasses companion bridge

This folder is the native edge of Slopify. The Python agent does **not** run on
the glasses. Meta's Wearables Device Access Toolkit (DAT) runs in an Android or
iOS phone app; that companion owns registration, permission and camera state,
then sends occasional JPEG observations to Slopify's LAN API.

This reference targets the official Android DAT **0.9.0** API. Its portable
transport and single-flight capture loop are compiled and tested here. The
small file under `android/reference/` is the DAT-specific hook to copy into
Meta's official CameraAccess sample. It is separated because resolving the
private GitHub Package requires your token and building the app requires an
Android SDK.

## The boundary

```text
Meta AI glasses
    ↓ camera stream
Android companion · DAT 0.9.0
    ↓ one JPEG about every 2 seconds
POST /api/wearables/v1/frames · raw image/jpeg
    ↓ Observation(source="meta_glasses")
existing change gate → perception → six strategies → judge → DJ → player
```

There is no second glasses algorithm. The response includes the same scene,
chosen track, reasoning, DJ action and playback state as the browser live path.
If perception is busy, the API returns `429` with `retry_after_ms`; the
companion waits instead of building a stale-frame queue.

## 1. Run Slopify on the LAN

Set the token before the server starts. It is deliberately absent from
`config.yaml` and source control.

```bash
export SLOPIFY_WEARABLE_TOKEN="$(openssl rand -hex 24)"
python run.py --serve --lan
```

Use the printed LAN address, normally `http://192.168.x.x:8420`. Confirm the
contract from another device:

```bash
curl http://YOUR_LAPTOP_IP:8420/api/wearables/v1/capabilities
```

Loopback development may omit the token. A server bound to `0.0.0.0` will
report `ready: false` and reject wearable frames until the token exists.

This hackathon setup uses HTTP on a trusted Wi-Fi network. Android therefore
needs cleartext traffic enabled in the debug manifest. Do not send a bearer
token over an untrusted network; use trusted TLS or a private tunnel outside a
local demo.

## 2. Prepare Meta's CameraAccess sample

Follow Meta's current Android setup, not an older `addStream` tutorial:

1. Join or create a Wearables Developer Center organization and project.
2. Install the Meta AI app, enable Developer Mode, and register the companion.
3. Give Gradle a classic GitHub token with `read:packages` as `GITHUB_TOKEN` or
   `github_token` in local properties. Never commit it.
4. Use DAT `0.9.0`, create a `DeviceSession`, request `Permission.CAMERA`, call
   `DeviceSession.addCamera(StreamConfiguration(...))`, then start
   `camera.stream`.
5. Test first with Meta's MockDeviceKit; then select registered glasses.

Meta's 0.9 CameraAccess sample currently targets Android API 31+ and Java 17.
The Device Access Toolkit is still a developer preview, so re-check its
changelog before changing the pinned version.

Official references:

- [Android DAT repository and setup](https://github.com/facebook/meta-wearables-dat-android)
- [Android DAT 0.9 changelog](https://github.com/facebook/meta-wearables-dat-android/blob/main/CHANGELOG.md)
- [Wearables developer documentation](https://wearables.developer.meta.com/docs/develop/)

## 3. Add the Slopify bridge

Copy these into the CameraAccess app under one package:

```text
android/src/main/kotlin/dev/slopify/meta/SlopifyWearablesClient.kt
android/src/main/kotlin/dev/slopify/meta/SlopifyCaptureLoop.kt
android/reference/MetaDat09SlopifyBridge.kt
```

After `addCamera(...)` succeeds and `camera.stream.start()` is called, retain
one bridge and start it with the screen's coroutine scope:

```kotlin
slopifyBridge = MetaDat09SlopifyBridge(
    stream = addedCamera.stream,
    backendUrl = BuildConfig.SLOPIFY_BACKEND_URL,
    bearerToken = BuildConfig.SLOPIFY_WEARABLE_TOKEN,
    clientId = Settings.Secure.getString(
        application.contentResolver,
        Settings.Secure.ANDROID_ID,
    ),
)
slopifyBridge.start(viewModelScope)
```

Call `slopifyBridge.stop()` whenever the camera or device session stops. Put
the URL and token in an ignored local property and expose them through
`BuildConfig`; do not paste either secret into Kotlin.

The reference bridge uses `Stream.capturePhoto()` because DAT already returns
`PhotoData.Bitmap` or `PhotoData.HEIC`. That produces a clean JPEG without
shipping every HEVC preview frame or adding a second decoder. The main camera
stream remains active exactly as Meta's sample requires.

Each bridge instance creates a fresh session UUID while keeping the device ID
stable. That lets its sequence restart at one after normal app recreation
without being mistaken for an old frame. A cancelled upload must fully complete
before `start()` will launch another loop, so blocking network IO cannot create
two senders.

## Protocol v1

`POST /api/wearables/v1/frames` has a raw JPEG body with `Content-Type:
image/jpeg` and these headers:

| Header | Meaning |
|---|---|
| `Authorization: Bearer …` | shared LAN token |
| `X-Slopify-Client-Id` | stable companion/device ID |
| `X-Slopify-Session-Id` | fresh UUID for this bridge launch |
| `X-Slopify-Sequence` | monotonically increasing frame number |
| `X-Slopify-Captured-At-Ms` | capture time, Unix milliseconds |
| `X-Meta-Dat-Version` | tested SDK version, currently `0.9.0` |

Duplicate and older sequences within one session are acknowledged without
another model call. The server authenticates before reading the raw body,
streams up to 5 MB, rejects images above 12 megapixels before OpenCV decode,
and processes one live frame at a time.

## What is and is not proven

Proven in this repository:

- thirteen FastAPI tests exercise authentication, metadata, session restarts,
  ordering, image validation, backpressure and the shared graph;
- five Kotlin/JVM tests compile the transport and prove its exact request,
  ordering, single-flight behavior and retry timing;
- the DAT-specific hook matches Meta's official 0.9 `addCamera` /
  `Camera.stream` / `capturePhoto()` API.

Still unproven: a signed companion has not been built with a developer project,
and no physical Meta glasses have sent a frame. On hardware, verify registration,
camera permission, firmware compatibility, Wi-Fi frame delivery, response
latency, and Bluetooth Spotify output before changing `STATUS.md` to Done.

The backend protocol is platform-neutral. An iOS companion can send the same
request from DAT 0.9, but this branch ships the Android reference bridge only.
