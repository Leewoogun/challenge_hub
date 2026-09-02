# Mobile Report — challenge-verification

> 🔴 **폐기 경고 — 이 문서의 재제출·캐시 서술은 더 이상 사실이 아니다.**
>
> - **재제출 = 전면 거부(`code=700` `이미 인증을 완료했어요`)** → **폐기.** 현행은
>   **`last-write-wins`** — 마감 전까지 무제한 교체, 마지막 등록본이 최종이다.
> - **재제출 재시도 전 status 선행 조회(회복 절차)** → **소멸.** 그냥 다시 올린다.
> - **사진 캐시 `max-age=86400`** → **`no-cache` + ETag/304.**
>
> 개정: [verification-photo-replace](../verification-photo-replace/spec.md) (2026-09-02).
> 🔴 **정본은 [api-contract.md](./api-contract.md) 와 [change-log.md](./change-log.md) 다.**
> 아래 본문은 2026-08 시점 기록으로 보존하며, **계약으로 인용하지 마라.**


- **작성일**: 2026-08-14 · **최종 갱신**: 2026-08-18
- **상태**: ✅ **T-M1·T-M2·T-M3 + 진입점 + EXIF 제거 완료** / ⏸ T-M4 미착수(범위 밖 지시)
- **계약**: [api-contract.md](./api-contract.md) — 🔴 **2026-08-18 개정본 기준**(multipart). [change-log.md](./change-log.md) 참조
- **입력**: [spec.md](./spec.md) · [ADR-0011](../../decisions/0011-photo-storage.md)(§3 supersede됨)
- **디자인**: ❌ 없음 — spec §5 대로 design-bridge 없이 진행. 아래 §디자인 전제 참조

> ## 🔴 이 문서를 읽는 법 (2026-08-18)
>
> 이 리포트는 **2026-08-14 작성분 위에 2026-08-18 갱신분을 얹은 것**이다.
> 그 사이 **사용자 결정으로 업로드 방식이 3단계 URL 발급 → multipart 단일 요청으로 바뀌었다.**
>
> **8/14 작성 절들 중 아래 넷은 이미 낡았다.** 지우지 않고 남긴 이유는 판단 경위가 근거로 남아야
> 하기 때문이며, 각 절 머리에 `⚠️ SUPERSEDED` 배너를 달아 뒀다:
> §데이터 계층(T-M3 기반) · §별도 `HttpClient` · §구현 도중 계약이 바뀌었다(409) · §API 계약 3쟁점 회신
>
> **현재 상태를 알려면 [§2026-08-18 갱신](#-2026-08-18-갱신--진입점--multipart-개편--exif-제거) 을 읽어라.**

---

## 구현 요약

### 2026-08-14 시점

챌린지 인증 사진의 **촬영(T-M1)과 업로드 전 리사이즈(T-M2)** 를 신규 모듈 `:core:camera` 로 구현했다.
서버 연동(T-M3·T-M4)은 **API 계약이 갈리는 지점 세 곳이 미확정**이라 착수하지 않았다 — spec §6 이
*"착수 전에 확정하라"* 고 못 박은 그 세 가지다.

**계약 무관 구간을 먼저 끝낸 것**이며, 대기 시간에 만든 코드가 계약에 따라 뒤집히지 않도록 경계를 그었다.

### 2026-08-18 시점 (현재)

계약 확정 후 **T-M3(업로드+제출)** 를 구 계약(3단계)으로 완성했고, 같은 날 **사용자 결정으로 업로드가
multipart 단일 요청으로 바뀌어 데이터 계층을 전면 개편**했다. 여기에 **인증 화면 진입점 연결**과
**업로드 전 EXIF 명시 제거**가 더해졌다.

**T-M4(상대 사진 보기)만 남았고, 이는 pm-lead 가 범위 밖으로 명시 제외한 것이다.**

---

## 사용한 모바일 레포 스킬

- **해당 스킬 없음** — challenge-app 의 `CLAUDE.md` Skill 매핑 테이블에 **신규 core 모듈 생성에
  대응하는 스킬이 없다.** `/full-feature` 는 Domain→Data→Feature→Navigation 전 레이어용이라 맞지
  않고, 이번 작업은 플랫폼 통합 인프라 한 겹이다.
- 대신 **`:core:permission` 모듈을 구조 템플릿으로 삼았다** — 가장 최근에 만들어진 core 모듈이고
  `androidMain`/`iosMain` expect/actual + 플랫폼 라이브러리 격리라는 같은 모양을 갖고 있다.
- 🔴 코드 편집은 전부 `cd challenge-app && claude -p` **child 위임**으로 수행했다
  (`.claude/agents/mobile-dev.md` 강제 규칙). 빌드·테스트는 본체가 background 로 실행했다.

> ⚠️ **하네스 갭으로 보고한다.** core 모듈 신설이 이번이 처음은 아닌데(`:core:push`, `:core:permission`)
> 스킬이 없다. 반복될 작업이면 스킬화 후보다. 백로그 판단은 pm-lead 몫.

---

## 변경된 파일

### 신규 — `:core:camera` 모듈

루트: `/Users/hwamulman/woogunProject/challenge/challenge-app/core/camera/`

| 파일 | 역할 |
|---|---|
| `build.gradle.kts` | `:core:permission` 미러링. androidMain 에만 `androidx.core.ktx`(FileProvider) · `androidx.activity.compose`(launcher) |
| `src/commonMain/.../PhotoScaling.kt` | 🔵 **순수 크기 계산** — `sampleSize` / `targetSize`. 이 모듈에서 플랫폼 없이 검증 가능한 유일한 지점 |
| `src/commonMain/.../CompressionSpec.kt` | 압축 파라미터 + `qualitySteps()`. `VERIFICATION` 기본값 보유 |
| `src/commonMain/.../CapturedPhoto.kt` | 업로드 준비된 JPEG 묶음 |
| `src/commonMain/.../PhotoCompressor.kt` | `interface` + `expect fun PhotoCompressor()` |
| `src/commonMain/.../CameraCapture.kt` | `expect @Composable rememberCameraCapture` + 결과 sealed interface |
| `src/androidMain/.../PhotoCompressor.android.kt` | 2단 디코드(`inSampleSize` → 정확 스케일) + **EXIF 회전** + 품질 루프 |
| `src/androidMain/.../CameraCapture.android.kt` | `TakePicture` + FileProvider. 원본 임시 파일 무조건 삭제 |
| `src/androidMain/AndroidManifest.xml` | CAMERA 권한 · `uses-feature required=false` · FileProvider |
| `src/androidMain/res/xml/camera_file_paths.xml` | `cache-path` 한정 |
| `src/iosMain/.../PhotoCompressor.ios.kt` | `drawInRect` 재렌더 + `UIImageJPEGRepresentation` 품질 루프 |
| `src/iosMain/.../CameraCapture.ios.kt` | `UIImagePickerController(sourceType = Camera)` + `NSObject` delegate |
| `src/commonTest/.../PhotoScalingTest.kt` | 13건 |
| `src/commonTest/.../CompressionSpecTest.kt` | 5건 |

### 수정

| 파일 | 변경 |
|---|---|
| `settings.gradle.kts` | `// Core` 섹션에 `include(":core:camera")` |
| `iosApp/iosApp/Info.plist` | `NSCameraUsageDescription` 추가 (한국어). 🔴 `NSPhotoLibrary*` 는 **의도적으로 넣지 않았다** — 아래 참조 |

---

## 테스트 결과

🔴 **XML 직접 read 로 확인.** timestamp 는 UTC (KST = +9h). 파일 mtime `8 14 10:33` 과 일치 — stale 아님.

| 타겟 | 클래스 | tests | failures | errors | XML timestamp |
|---|---|---|---|---|---|
| `testDebugUnitTest` | `PhotoScalingTest` | **13** | 0 | 0 | `2026-08-14T01:33:17.014Z` |
| `testDebugUnitTest` | `CompressionSpecTest` | **5** | 0 | 0 | `2026-08-14T01:33:16.983Z` |
| `iosSimulatorArm64Test` | `PhotoScalingTest` | **13** | 0 | 0 | `2026-08-14T01:33:10.700Z` |
| `iosSimulatorArm64Test` | `CompressionSpecTest` | **5** | 0 | 0 | `2026-08-14T01:33:10.667Z` |

- **단위: 18/18 passed × 2 플랫폼**
- **Android 빌드**: ok (`:core:camera:compileDebugKotlinAndroid`)
- **iOS 빌드**: ok (`:core:camera:compileKotlinIosSimulatorArm64`)
- **전체 회귀(267 기준선)**: 아래 §회귀 참조

### 회귀 — 🔵 **기준선 267 그대로, 회귀 0**

`./gradlew testDebugUnitTest` (전 모듈) — `BUILD SUCCESSFUL in 2m 35s`, 993 tasks.

XML 30개를 전수 합산했다 (`-newermt "2026-08-14 10:30"` 로 **이번 실행분만** 골라 stale 배제):

| | 값 |
|---|---|
| **전체** | **285 tests / 0 failures / 0 errors** |
| 이번 신규(`:core:camera`) | 18 |
| **285 − 18** | **= 267** — 🔵 **기준선과 정확히 일치. 기존 테스트 회귀 0건** |

모듈별 내역(발췌): `feature:home` 20 · `feature:challenge:create` 20 · `remote:mapper` 58(6클래스) ·
`feature:challenge:oath` 17 · `remote:datasource` 22 · `feature:login` 15 · `feature:challenge:detail` 14 ·
`feature:friends:search` 12 · `feature:friends:list` 11 · `core:push` 9 · `feature:main` 9 ·
`core:utils` 28(4클래스) · `data:repositoryImpl` 14(3클래스) · `remote:network` 7 · `remote:model` 6 ·
`core:ui` 4 · `composeApp` 1 · **`core:camera` 18(신규)**

---

## 구현 판단과 근거

### T-M1 — 시스템 카메라 + expect/actual

**Android `ActivityResultContracts.TakePicture` / iOS `UIImagePickerController(sourceType = Camera)`.**
`push-fcm` 결정사항 8번(**KMP 커뮤니티 래퍼 미사용 — 네이티브 + expect/actual**)에 정합한다.

**CameraX 를 기각한 이유**: 새 의존성이 필요하고, 무엇보다 **디자인이 없다**(spec §5). 자체 카메라
UI 는 프리뷰·셔터·전후면 전환을 전부 발명해야 하는데 **디자인이 나오면 통째로 버려진다.**
시스템 카메라는 화면을 발명하지 않아도 되고, 부수 효과로 **갤러리 진입점이 구조적으로 없다.**

### 🔴 갤러리 차단 — 코드 0건 + plist 로 이중 차단

기획서 §2.5 요구사항이다.

- `ACTION_PICK` / `PickVisualMedia` / `UIImagePickerControllerSourceTypePhotoLibrary` **전부 0건**
- 🔵 iOS `Info.plist` 에 **`NSPhotoLibraryUsageDescription` 을 일부러 선언하지 않았다.**
  나중에 누가 갤러리를 붙이려 해도 **plist 부터 걸려서 조용히 들어오지 못한다.** 없는 키가
  방어 장치 역할을 하는 자리라 이 판단을 plist 주석에 남겼다

### 권한 — `:core:camera` 는 `:core:permission` 에 의존하지 않는다

`AppPermission.CAMERA` 와 `PermissionManagerImpl` 의 moko 매핑은 **이미 있었다**(§선행 상태 참조).
그래서 `:core:camera` 는 권한을 요청하지 않고, **호출부가 권한을 얻은 뒤 `capture()` 를 부른다.**

의존을 끊은 이유: 의존하면 **권한 UX 결정(재요청·설정 이동 안내)이 이 모듈로 새어 들어온다.**
그 결정은 화면의 것이다. `MainViewModel` KDoc 이 이미 *"기능이 막히는 권한(카메라)에서만 안내
다이얼로그를 쓴다"* 고 방침을 적어 뒀고, 그 판단 주체는 화면 쪽이다.

⚠️ CAMERA 권한을 매니페스트에 선언하면 **시스템 카메라 인텐트조차 앱의 권한 보유를 요구한다.**
즉 권한 없이 `capture()` 를 부르면 실패한다 — 이 결합을 매니페스트 주석에 명시했다.

### 🔴 원본 바이트를 commonMain 으로 올리지 않는다

플랫폼 경계는 **이미 축소·재압축된 JPEG 만** 넘긴다. 원본을 공통 계층으로 올리면 수 MB 배열이
그대로 힙에 뜨는데, 이건 **ADR-0011 이 base64 를 기각한 것과 같은 종류의 실수**다.
`PhotoCompressor` 가 파일 **경로**를 받는 것도 같은 이유다.

### iOS — 스텁이 아니라 실구현

spec T-M1 이 *"iOS 는 `push-fcm` 처럼 스텁으로 두고 Android 우선해도 된다"* 를 허용했으나 **쓰지 않았다.**

`push-fcm` 의 iOS 스텁에는 **외부 블로커**가 있었다 — APNs 인증키가 유료 Apple Developer Program
전용이라 코드로 넘을 수 없었다(`FcmTokenProviderIos` KDoc). **카메라에는 그런 블로커가 없다.**
UIKit 은 Kotlin/Native 에 그대로 노출돼 있어 스텁으로 둘 근거가 서지 않았다.

⚠️ **한계**: iOS 시뮬레이터에는 카메라가 없어 `isSourceTypeAvailable` 에서 `NO_CAMERA` 로 빠진다.
즉 **컴파일과 단위 테스트는 검증했으나 iOS 촬영 실동작은 실기기가 필요하다.** T-I1 범위다.

---

## 🔴 T-M2 리사이즈 — 목표치와 실측값

### 목표치 (코드에 확정된 값)

| 항목 | 값 | 근거 |
|---|---|---|
| 장변 최대 | **1440 px** | 인증 사진은 "무엇을 했는지" 확인용이라 원본 해상도가 불필요 |
| 목표 크기 | **512,000 B (500 KB)** | ADR-0011 *"장당 ~500KB 목표"* |
| 품질 사다리 | **85 → 75 → 65 → 55 → 50** | 목표 이하가 되면 즉시 중단 |

### ❌ 실측값 — **못 냈다. 추정으로 채우지 않았다**

세 가지가 동시에 막았다:

1. **Android JPEG 인코더는 기기·에뮬레이터에서만 돈다.** `Bitmap.compress` 는 JVM 단위 테스트에서
   실행 자체가 안 된다
2. **Robolectric 은 답이 아니다.** 카탈로그에 4.14.1 이 등록돼 있으나 **레포 전체 사용처가 0건**이고,
   애초에 Robolectric 의 `Bitmap` 은 shadow 라 **실제 인코딩을 하지 않아 바이트 수가 가짜다**
3. **프로젝트에 실사진 자산이 0건**이다(검색 결과 65KB 로고 png 하나뿐). 합성 이미지로 재면
   노이즈는 과대, 그라데이션은 과소로 나와 **대표성 없는 숫자**가 된다

### 대신 한 것 — 자동 계측

압축 **성공 경로에 한 줄** 로그를 넣었다. 양 플랫폼 동일 형식이다:

```
인증 사진 압축 실측: 원본 {bytes}B {w}x{h} -> 결과 {bytes}B {w}x{h}, quality={q}, 목표 512000B 초과={bool}
```

→ **T-I1 실기 검증에서 촬영 한 번만 하면 숫자가 저절로 남는다.** 사람이 따로 재야 하는 일을
없앤 것이고, 그때 이 표를 채운다.

⚠️ `Logger.i` 는 `isDebug` 일 때만 나간다 — 개발용 계측이고 운영 로그가 아니다.

### ⚠️ 500KB 는 상한 보장이 아니라 목표다

최저 품질(50)로도 목표를 못 맞추면 **그 결과를 그대로 쓴다.** `null` 로 버리면 사용자가 인증
자체를 못 하기 때문이다. 초과 여부는 위 로그에 `초과=true` 로 남는다.

🔵 **서버 상한은 5 MiB 로 확정됐고, 앱 목표(~500KB)와 의도적으로 다르다.** 두 값을 같게 만들면
*"압축이 목표를 못 맞춘 정상 사진"* 이 거부되어 **사용자가 인증 자체를 못 한다** — `null` 로 버리지
않기로 한 판단과 정확히 같은 축이다. 10배 헤드룸이 맞는 간격이다.

**→ 자동 재압축 분기는 넣지 않는다.** 근거는 아래 §413 참조. 계약 §2 도 같은 결론이다.

---

## 리뷰에서 찾아 고친 것

### 1. 🔴 회전 시 촬영 결과가 조용히 사라지는 경로

촬영 파일 경로를 `remember` 로 들고 있었다. `MainActivity` 에는 `android:screenOrientation` 도
`android:configChanges` 도 없어 **시스템 카메라가 떠 있는 동안 기기를 돌리면 Activity 가 재생성된다.**
`rememberLauncherForActivityResult` 는 `ActivityResultRegistry` 가 복원해 주는데 **우리 상태만 날아가서**
콜백이 이른 `return` 으로 빠진다 → **사진을 찍었는데 아무 일도 안 일어나고 예외도 로그도 없다.**

`rememberSaveable` 로 고쳤고 되돌리지 않도록 실패 모드를 주석에 남겼다.

> 🔵 **가정 방어가 아니다.** 매니페스트를 실제로 확인해 도달 가능함을 확인한 뒤 고쳤다.
> spec 수용 기준의 *"업로드 실패가 조용히 삼켜지면 안 된다"* 와 같은 계열의 실패 모드다.

### 2. EXIF 회전

시스템 카메라 결과물은 방향을 **EXIF 에만** 담는 경우가 많고, 재인코딩하면 EXIF 가 사라져
**세로로 찍은 사진이 눕는다.** Android 는 픽셀을 직접 회전시켰고, iOS 는 `UIImage` 가 방향을
이미 반영하므로 불필요하다 — **두 구현이 달라 보이는 이유**를 양쪽 주석에 남겼다.

---

## 선행 상태 정정 — 카메라 배관은 예상보다 깔려 있었다

pm-lead 브리핑과 spec §0.3 이 *"`moko-permissions-camera` 는 `libs.versions.toml` 에 등록만 돼 있다"*
고 적었으나, 실측 결과 **더 들어와 있었다.**

| 항목 | 실제 상태 |
|---|---|
| `AppPermission.CAMERA` enum | ✅ 있음 — KDoc 이 *"챌린지 인증 사진 촬영"* 으로 이 feature 를 지목 |
| `PermissionManagerImpl` 의 CAMERA 매핑 | ✅ 있음 (`moko.permissions.camera.CAMERA` import 포함) |
| `core/permission/build.gradle.kts` 의존 | ✅ toml 등록만이 아니라 실제 `implementation` |
| `MainViewModel` 의 카메라 권한 UX 방침 | ✅ KDoc 에 미리 적혀 있음 |
| **`AndroidManifest` CAMERA 권한** | ❌ 없었음 → 이번에 `:core:camera` 모듈 매니페스트로 추가 |
| **촬영 코드** | ❌ **0건** (grep 확인) → 이번에 신규 |

→ **권한 요청 계층은 재사용했고 촬영 계층만 새로 만들었다.** spec 의 "없는 것" 목록은
촬영 코드 쪽이 맞았다.

---

## ✅ 데이터 계층 (T-M3 기반) — 33/33 passed

> ⚠️ **SUPERSEDED (2026-08-18)** — 이 절의 테스트 숫자와 구조는 **구 계약(3단계 URL 발급) 기준**이다.
> multipart 개편으로 이 데이터 계층은 상당 부분 삭제·재작성됐다. 현재 숫자는
> [§2026-08-18 갱신](#-2026-08-18-갱신--진입점--multipart-개편--exif-제거) 을 보라.
> **판단 경위 기록으로만 남긴다.**

XML 직접 read, timestamp UTC. `BUILD SUCCESSFUL in 34s`.

| 클래스 | tests | failures | XML timestamp |
|---|---|---|---|
| `VerificationWireFixtureTest` | **8** | 0 | `2026-08-14T02:01:09.542Z` |
| `VerificationMappersTest` | **9** | 0 | `2026-08-14T02:01:09.529Z` |
| `VerificationRemoteDataSourceImplTest` | **16** | 0 | `2026-08-14T02:01:17.059Z` |

🔵 `VerificationWireFixtureTest` 는 **계약 표에서 파생된 테스트**다 — 라이브 응답이 아니라
**null 최대 픽스처**(`PENDING` party 의 세 필드가 명시적 `null`, **키는 존재**)를 JSON 원문에서
도메인까지 태운다. soul-oath §3.1 이 세운 규칙 그대로다.

### 🔴 별도 `HttpClient` — 계약 §0.2 를 지키려면 필수였다

> ⚠️ **부분 SUPERSEDED (2026-08-18)** — **업로드에는 더 이상 해당하지 않는다.** multipart 제출이
> Bearer 필수인 평범한 인증 엔드포인트가 되어 **기본 클라이언트를 그대로 탄다.**
> 🔴 **그러나 §5 사진 서빙에는 이 논거가 그대로 살아 있다** — 아래 §서빙 전용 클라이언트 참조.
> 즉 이 절의 추론은 맞았고, **적용 범위만 §3 에서 §5 로 좁혀졌다.**

`@Named(SIGNED_URL_HTTP_CLIENT)` 로 등록. `Auth`·`DefaultRequest` 없이 `HttpNetworkLogger` 만.

**형식적 조항이 아니었다.** 기존 클라이언트의 Auth 설정이 이렇다:

```kotlin
sendWithoutRequest { request -> request.url.pathSegments.none { it == "auth" } }
```

→ **경로에 `auth` 가 없는 모든 요청에 Bearer 를 선제 전송한다.** `/api/v1/photos/...` 에는 `auth` 가
없으므로 재사용하면 **계약 위반이 자동 발생**한다. 게다가 `install(DefaultRequest)` 가
`Content-Type: application/json` 을 강제해 §2 의 `image/jpeg` 와 충돌한다.

데이터소스 테스트가 **`Authorization` 부재를 MockEngine 실요청으로 단언**한다.
**왜 합치면 안 되는지**를 KDoc 에 남겨 나중에 "중복이네" 하고 합치는 것을 막았다.

### 매퍼 판단 — "못 읽은 것" vs "없는 게 사실"

`ChallengeDetailMapper` 의 선례(`deadline` vs `contract: null`) 기준을 적용했다.

| 대상 | 처리 | 근거 |
|---|---|---|
| ① `expiresAt` 파싱 실패 | **전체 매핑 실패** | 만료를 모르는 업로드 대상은 유효성 판단이 불가능하다 (`deadline` 선례) |
| ④ `photoUrl` ↔ `photoUrlExpiresAt` | **쌍째로 null 강등** | 만료를 못 읽은 URL 을 통과시키면 유효하다고 오판한 채 403 을 맞는다. 전체 실패로 승격하지 않은 이유: 상대편의 멀쩡한 현황까지 버리게 되고, "VERIFIED 인데 URL 없음"은 만료 상태와 같아 재조회로 자연 회복된다 |
| ④ `PENDING` 의 셋 다 null | **그대로 통과** | 없는 게 사실이다 (`contract: null` 선례) |
| 모르는 `status` 문자열 | `PENDING` 으로 흡수 | 서버가 상태를 추가해도 조회가 안 깨진다. `PENDING` 은 사진을 날조하지 않는 보수적 기본값. DTO 를 `@Serializable` enum 으로 받지 않은 이유도 같다 — 모르는 wire 값에서 역직렬화 **전체**가 터진다 |

---

## 🔴 구현 도중 계약이 바뀌었다 — §2 에 `409` 추가

> ⚠️ **SUPERSEDED (2026-08-18)** — **§2(PUT) 엔드포인트 자체가 삭제됐다.** 409 방어는 위협 모델이
> 소멸해 계약에서 제거됐다(앱이 key 를 보지도 못하고 업로드 URL 이라는 것 자체가 없어졌다).
> 앱의 409 fold 코드도 `PhotoUploadStatusMapper.kt` 째로 삭제했다.
> **판단 경위 기록으로만 남긴다.**

`verif-backend` 가 **자기 구현의 결함을 찾아 고쳤고**, 그 결과 업로드 응답에 `409` 가 생겼다.

**결함**: 업로드 URL 이 제출 확정 뒤에도 만료(10분)까지 살아 있어, **상대에게 알림이 간 뒤
같은 URL 로 다른 바이트를 올려 상대가 이미 본 사진을 바꿔치기**할 수 있었다. `verifications`
row 는 그대로라 **흔적이 남지 않는다.** 계약 §3 이 막으려던 재제출 정책이 **§2 로 새고 있었다.**
1차 PUT 204 / 2차 PUT 204 로 재현까지 됐다.

### 앱 반영 — 🔵 409 를 `Success` 로 **접었다**

새 결과 타입을 만들지 않았다. 근거:

1. 204 와 409 모두 *"온전한 바이트가 서버에 있다"* 가 참이고 **§3 진입 조건이 동일**하다
2. 타입을 갈라 두면 호출부마다 `|| result is AlreadyUploaded` 를 빠뜨릴 자리가 생긴다.
   **한 곳만 빠져도 "업로드는 됐는데 제출이 안 되는" 상태로 사용자가 갇힌다**
3. 🔴 접어도 안전한 근거는 **서버의 원자적 쓰기** — 전송이 끊기면 잘린 파일이 안 남아 409 가
   아니라 204 다. 즉 **409 가 곧 온전한 바이트를 뜻한다.** 원자적이 아니었으면 접으면 안 됐다

테스트 이름에 의도를 박았다 — `uploadPhoto 409 - 응답 유실 후 재시도로 이미 온전한 바이트가
서버에 있다는 뜻이라 Success 로 접는다`. 나중에 버그로 오인해 되돌리는 것을 막기 위해서다.

> 🔵 이사 시에도 앱은 무변경이다. 409 를 성공으로 접어 뒀으므로 오브젝트 스토리지가 409 를
> 주지 않고 204 만 줘도 동작이 같다. (서버 쪽은 버킷 정책으로 옮겨야 하며 이사 체크리스트에 등재됐다)

---

## API 계약 — ✅ `confirmed`

> ⚠️ **부분 SUPERSEDED (2026-08-18)** — 세 쟁점 중 **①업로드 방식과 ②재제출 정책이 재확정**됐다.
> ①은 URL 발급 → **multipart 단일 요청**, ②는 *"같은 key 멱등"* → 🔴 **전면 거부**(key 왕복이
> 사라져 멱등 판별이 불가능해졌다). **③조회 위치(별도 엔드포인트)만 그대로다.**
> 아래 §쟁점 2 의 *"내 안(단순 거부)보다 낫다"* 는 평가는 **결과적으로 뒤집혔다** — 최종 정책은
> 내가 처음 제안했던 **단순 거부**다. 다만 그 근거는 내 원안의 근거가 아니라 *"멱등 판별 수단
> 소멸"* 이라는 새 사실이다. **판단 경위 기록으로 남긴다.**

spec §6 이 지목한 세 쟁점이 전부 확정됐다. **계약서 소유자는 backend-dev 다.**

> 🔵 **쟁점 3 에서 내 주장이 틀렸고 철회했다.** 나는 `GET /challenges/{id}` 에 얹자고 했고
> 근거는 *"만료 URL 갱신이 공짜"* 였다. 얹으면 **계약서·서명이 든 큰 응답 전체의 수명이 10분**이
> 되고 사진 하나 갱신하려고 계약서를 통째로 다시 받게 된다 — **내가 "공짜"라 부른 것이 실은
> 갱신을 비싸게 만드는 것**이었다. 내 진짜 우려(만료를 이미지 로드 실패로만 감지 → 네트워크
> 오류와 구분 불가)는 **`photoUrlExpiresAt` 이 party 별로 실리면서 우회가 아니라 원인이 제거**됐다.
>
> 🔴 **부수적으로, 별도 엔드포인트가 §3.4 우려를 통째로 없앴다** — `challenger`/`opponent` 객체가
> **절대 null 이 아니다.** 얹기 안이었다면 미수락 챌린지에서 `verification: null` 이 생겨
> **`contract: null`(#24)과 똑같은 실패 모드가 반복**됐을 것이다. 내 안대로 갔으면 그 사고를
> 다시 만들었다.
>
> 재제출도 backend 안(**같은 key 멱등** / 다른 key 거부)이 내 안(단순 거부)보다 낫다 —
> 내 안대로면 **§3 응답만 유실된 네트워크 재시도가 사용자에게 실패로 보였을 것**이다.

### 1. 업로드 방식 — URL 발급(ADR-0011 §3)에 동의. 다만 **URL 의 성질**을 명시 요청

- 🔴 **업로드 응답은 BaseResponse 가 아니다.** 이 앱의 모든 호출은 `ApiResultCall` 이
  `body.code == 200` 으로 판정하는데(ADR-0002), 업로드는 임의 절대 URL 이라 **Ktorfit 을 안 탄다.**
  **HTTP status 로 판정**해야 하고, 오브젝트 스토리지로 옮기면 스토리지가 BaseResponse 를 만들어
  줄 리 없으므로 **지금부터 status 기반이어야 이사 시 앱이 무변경**이다
- 🔴 **uploadUrl 에 우리 JWT 를 붙이지 않는다.** presigned URL 에 알 수 없는 `Authorization`
  헤더를 보내면 S3 는 서명 검증에서 거부한다 — **§3 이 막으려던 바로 그 부채**다.
  URL 자체가 자격을 담아야 하고, 모바일은 업로드용 **별도 HttpClient** 를 써서 Ktor Auth(bearer)
  인터셉터가 토큰을 자동 주입하지 않게 한다
- `PUT` + raw body + `Content-Type: image/jpeg`. 절대 URL. `photoKey` 는 **서버가 만든다**
  (앱이 만들면 T-B1 의 경로 탈출 방어가 무의미해진다)
- **최대 허용 바이트**와 **TTL** 요청 — 위 §T-M2 참조

### 2. 재제출 정책 — 🔵 **거부(첫 제출만 인정)** 제안

**T-M3 의 재시도 요구는 이 결정과 무관하다** — 업로드가 실패하면 제출 확정이 안 일어났고 row 는
`PENDING` 그대로라, 어느 정책이든 재시도는 된다. 쟁점은 순수하게 *"이미 `VERIFIED` 인데 또 제출하면?"* 이다.

거부를 제안한 이유 셋:
1. **상대에게 이미 알림이 갔고 상대가 봤을 수 있다.** 덮어쓰기면 상대가 본 사진을 사후 교체할 수
   있고, "무를 수 없는 약속" 컨셉과 어긋난다 — `soul-oath` 가 서명 백필을 *"없던 맹세의 날조"* 라며
   거부한 것과 같은 축
2. 덮어쓰기면 **`OPPONENT_VERIFIED` 중복 발송** 여부를 또 정해야 한다
3. 덮어쓰기면 **이전 파일이 고아로 남는다** (ADR-0011 이 보관 정책을 미결로 넘긴 상태)

**대가와 모바일 대응**: 오촬영을 못 고친다 → **모바일이 제출 전 확인 화면을 넣는다**
(촬영 → 미리보기 → "이 사진으로 인증"). 계약과 무관한 내 쪽 작업이다.

### 3. 조회 위치 — 🔵 **기존 `GET /challenges/{id}` 에 얹기** 제안

- 🔴 **결정적 이유: 만료 URL 갱신이 공짜다.** 읽기 URL 이 상세 응답 안에 있으면
  **재진입 = 재조회 = 새 URL** 이라 별도 장치가 0 이다. 별도 엔드포인트면 모바일이 만료를
  **이미지 로드 실패로만 감지**하게 되어 네트워크 오류와 구분이 안 된다
- **접근 제어를 상속한다** — `GET /challenges/{id}` 는 이미 당사자 아니면 700 이라 ADR-0011 §4 가
  새 코드 없이 만족된다
- **shape**: `challenger`/`opponent` **안에 중첩**한다. soul-oath §3 이 *"역할 그대로 준다"* 를
  확정했고 `ChallengeDetailViewModel` 이 이미 관점을 판정하고 있어, `my*`/`opponent*` 로 뒤집어
  주면 한 응답에 두 관점이 섞인다
- 🔴 **nullable 전수 표(§3.1) 등재 필수** — `verification` 자체가 `null` 일 수 있다(row 는
  `accept()` 때 생기므로 미수락 챌린지엔 없다). **`contract: null` 과 완전히 같은 실패 모드**다
- ⚠️ `confirmed` 계약 변경이므로 **`change-log.md` 등재가 필수**임을 인지하고 있다

### 4. `OPPONENT_VERIFIED` — §0.6.1 통지 회신함

- **모바일 조치**: `PushEvent` 에 타입 추가 예정. 목적지는 **`Route.Challenge.Detail(challengeId)`**
  를 제안했고 **판정은 pm-lead** 에게 넘겼다
- 🔴 **`NotificationMessages.of()` 에 문구를 넣기 전에 통지해 달라고 회신했다.** 내 `PushEvent.from`
  변경 전에 발송이 시작되면 **알림을 눌러도 아무 데도 안 가고 크래시도 로그도 없다**
- `data.challengeId` 가 이 타입에도 실려야 한다 — `PushEvent.from` 이 `challengeId` 없으면 이벤트를
  버린다

---

## ✅ `OPPONENT_VERIFIED` — §0.5 게이트 해제 완료

계약 §0.5(= push-fcm §0.6.1)가 **처음 실제로 발동한 건**이다. 서버가 `NotificationMessages.of()` 에
문구를 넣기 전에 앱이 타입을 알아야 한다 — 모르면 **알림을 눌러도 아무 데도 안 가고 크래시도
로그도 남지 않는** 무증상 실패가 난다.

계약이 요구한 두 조건을 충족하고 `verif-backend` 에 **"발송 개시해도 된다"** 를 회신했다.

| 계약 §0.5 조건 | 상태 |
|---|---|
| ① `PushEvent.from` 이 `type = "OPPONENT_VERIFIED"` 를 아는가 | ✅ `PushEvent.OpponentVerified(challengeId)` + `from()` 분기 |
| ② 그 딥링크가 챌린지 상세로 가는가 | ✅ `MainViewModel.toRoute()` → `Route.Challenge.Detail(challengeId)` |

**목적지 근거** (pm-lead 판정과 독립적으로 같은 결론): 상대 사진을 볼 수 있는 화면이 **상세뿐**이고
T-M4 가 거기에 붙인다. 홈 카드는 상태 뱃지만 보여줘 한 번 더 탭해야 한다.
🔵 **`ChallengeRejected → Home` 과 대비되는 자리다** — 거기는 *"계약서가 없어 상세에 볼 것이 없다"*
였고, 여기는 **볼 것이 생긴다.**

🔵 **`toRoute()` 는 `else ->` 없는 exhaustive `when` 으로 유지**했다. 다음에 또 새 타입이 생기면
**컴파일러가 목적지 지정을 강제**한다 — §0.6.1 규약의 코드 쪽 짝이다.

**실측** (XML 직접 read, timestamp UTC):

| 클래스 | tests | failures | 증분 | XML timestamp |
|---|---|---|---|---|
| `PushEventTest` | **10** | 0 | 9 → 10 (+1) | `2026-08-14T01:42:16.411Z` |
| `MainViewModelTest` | **10** | 0 | 9 → 10 (+1) | `2026-08-14T01:42:37.929Z` |

⚠️ **stale 판정 사례 1건**: 첫 확인 때 `MainViewModelTest` XML 이 `01:36` 이었다 — 직전 전체 회귀
실행분이라 **이번 변경 이전 결과**였다. 빌드 완료를 기다려 `01:42` 로 갱신된 것을 확인하고 채택했다.

---

## 🔴 T-M4 선행 발견 — **이 앱은 원격 이미지를 한 번도 로드한 적이 없다**

spec 에도 브리핑에도 없던 사실이라 착수 전에 적어 둔다. **T-M4 는 "사진을 보여준다" 한 줄이 아니다.**

| | 상태 |
|---|---|
| `coil` 3.2.0 · `coil-network-ktor3` · `coil-test` | ✅ `libs.versions.toml` 에 **등록만** 돼 있음 |
| 레포 전체 coil 사용처 | ❌ **0건** (`build.gradle.kts` 의존 선언 포함 0건) |
| `AsyncImage` / `rememberAsyncImagePainter` / `ImageLoader` | ❌ **0건** |
| `profileImageUrl` 을 실제로 그리는 코드 | ❌ 없음 — **닉네임 이니셜 placeholder** 로 대체 중 |

**코드가 스스로 증언한다** — `feature/friends/search` 의 `FriendSearchItem` KDoc:
> *"이미지 로더 부재로 `profileImageUrl` 은 시그니처에만 받고 닉네임 이니셜 placeholder 로 렌더한다."*

즉 `profileImageUrl` 은 도메인·DTO·State 를 타고 화면까지 오지만 **그리는 단계가 없다.**

### 이것이 T-M4 에 뜻하는 것

**인증 사진이 이 앱의 첫 원격 이미지가 된다.** 필요한 선행 작업:

1. **`ImageLoader` 초기화** — KMP 전역. Coil 3 는 `SingletonImageLoader.setSafe` 로 잡는다
2. **Ktor 네트워크 fetcher 배선** — `coil-network-ktor3` 를 기존 `HttpClient` 에 물릴지 별도로 둘지
   결정 필요. 🔴 **기존 클라이언트를 재사용하면 Ktor Auth(bearer) 가 사진 URL 에도 토큰을 붙인다** —
   업로드 URL 에서 JWT 를 떼자고 계약에 요청한 것과 **같은 문제가 조회 쪽에서 재발**한다.
   **별도 클라이언트가 맞다고 본다**
3. **디스크 캐시 키** — 만료 토큰이 URL 에 붙으면 매 조회마다 키가 달라져 같은 사진을 다시 받는다.
   계약에 *"경로 고정 + 토큰은 쿼리"* 를 부탁했고, 안 되면 `challengeId+userId+verifiedAt` 로
   캐시 키를 직접 지정해 우회한다

> 🔵 **부수 효과**: 이 배선이 들어가면 `profileImageUrl` placeholder 들이 전부 살아날 수 있다.
> 다만 **그건 이 feature 의 범위가 아니다** — 배선만 하고 기존 화면은 건드리지 않는다.
> 범위를 넓힐지는 pm-lead 판단이며, 백로그 후보로 남긴다.

⚠️ `moko-permissions-camera` 와 **똑같은 패턴**이다 — 카탈로그에 등록해 두고 배선은 안 한 상태.
카탈로그 등록을 "준비됨" 으로 읽으면 스코프를 과소평가하게 된다.

---

## 🔴 디자인 전제 (spec §5)

**Lovable 에 카메라/인증 route 가 0건**이라 design-bridge 없이 진행했다.

이번 범위(`:core:camera`)는 **화면이 아니라 플랫폼 통합 계층이라 디자인 영향이 없다** —
촬영 UI 는 시스템 카메라가 그린다. 디자인 의존은 **T-M3/T-M4 의 인증 화면·상세 사진 영역**에서
발생하며, 그때 `:core:designsystem` 토큰과 기존 화면 패턴을 따라 만들고
**디자인이 나오면 교체한다는 전제**로 진행한다(`soul-oath` 와 같은 상태).

---

## 🔴 2026-08-18 갱신 — 진입점 + multipart 개편 + EXIF 제거

pm-lead 지시로 세 덩어리를 수행했다. **전부 커밋 전 working tree 상태다.**

### A. Verify 화면 진입점 연결

**문제**: `:feature:challenge:verify` 모듈·`Route.Challenge.Verify`·`MainScreen` 의 `NavDisplay` 등록이
모두 있었으나 **어느 화면도 그 Route 로 navigate 하지 않아 인증 화면에 도달할 방법이 없었다.**
네비게이션 3요소 중 **비어 있던 호출부 하나만** 채웠다.

| 파일(`:feature:challenge:detail`) | 변경 |
|---|---|
| `contract/ChallengeDetailState.kt` | `STATUS_IN_PROGRESS` 상수 + `Data.canVerify: Boolean` |
| `ChallengeDetailViewModel.kt` | `toData()` 에서 `canVerify = status == STATUS_IN_PROGRESS` 확정 |
| `component/ChallengeDetailContract.kt` | `onVerifyClick` + 하단 고정 CTA. 레이아웃을 스크롤 영역 + 고정 푸터로 재구성 |
| `ChallengeDetailScreen.kt` | `onVerifyClick` 관통 |
| `ChallengeDetailRoute.kt` | `navigator.navigateTo(Route.Challenge.Verify(challengeId))` |

**UI**: `IN_PROGRESS` 일 때만 상세 화면 **하단에 고정된** primary CTA(`IconTextButton`, "인증하기",
`Icons.Filled.PhotoCamera`, `bold16`). 계약서가 길어져도 주 액션이 스크롤에 묻히지 않게 스크롤 밖에 뒀다.
디자인 없음 전제(spec §5)라 designsystem 토큰과 기존 화면 패턴을 따랐고 **디자인 나오면 교체 대상**이다.

🔴 **판별을 Composable 에서 하지 않았다** — CLAUDE.md 의 *"Composable 에서 조건 판별 금지"* 에 따라
ViewModel 매핑 시점에 `canVerify` 로 확정한다.

**`build.gradle.kts` 변경 0건** — 컨벤션 플러그인이 `:core:navigation` 을, Refresh 아이콘 때문에 이미
선언돼 있던 `materialIconsExtended` 가 카메라 아이콘을 커버한다.

**백스택**: 수정 불필요. `VerifyViewModel.complete()` → `NavigateBack` → `popBackStack()` 으로 상세 복귀.
상세가 아직 인증 상태를 표시하지 않아 복귀 시 갱신할 것도 없다. **Verify 모듈은 한 줄도 수정하지 않았다.**

### B. 🔴 업로드 multipart 전면 개편

사용자 결정(2026-08-18)으로 ADR-0011 §3 이 supersede 됐다. **구 계약(3단계)으로 이미 만들어 둔
데이터 계층을 전부 뜯었다.** 커밋 전이라 부채로 남지 않았다.

**삭제 5** — `PhotoUploadStatusMapper.kt` · `VerificationUploadUrlResponse.kt` · `SubmitVerificationBody.kt`
· `VerificationUploadTarget.kt` · `PhotoUploadResult.kt`
**생성 2** — `VerificationSubmitOutcome.kt` · `FakeUserInfoRepository.kt`(verify commonTest)
**수정 12** — `VerificationApi`(multipart) · `KtorfitModule` · `NetworkQualifiers` · `VerificationMappers`(+테스트 2)
· `VerificationRemoteDataSourceImpl`(+테스트) · `VerificationRemoteDataSource` · `VerificationRepository`
· `VerificationRepositoryImpl` · `ChallengeVerifications`(`partyOf` 헬퍼) · `VerifyViewModel`
· `FakeVerificationRepository` · `VerifyViewModelTest` · `remote/datasource/build.gradle.kts`

#### 핵심 설계 — 제출을 콜백에서 반환값으로

```kotlin
sealed interface VerificationSubmitOutcome {
    data class Success(val result: VerificationSubmitResult)
    data class Rejected(val message: String)    // 서버가 code 로 판정해 거부. 재시도해도 같다
    data class Unreachable(val message: String) // 전송이 끊겨 서버 반영 여부를 모른다
}
```

`onError(String)` 한 채널로는 **거부와 "모름"을 구분할 수 없는데 앱의 조치가 정반대**다.
삭제된 `PhotoUploadResult` 가 같은 이유로 반환값이었다.

| `ApiResult.Failure` | 분류 | 근거 |
|---|---|---|
| `CustomError` | `Rejected` | 서버가 code 로 판정했다 |
| `NetworkError` · `UnknownApiError` | `Unreachable` | 전송 실패 |
| 🔴 **`HttpError`(예: 500)** | 🔴 **`Unreachable`** | **커밋 이후에 실패했을 수 있어 반영 여부를 모른다.** 거부로 분류하면 §4 확인이 돌지 않는다 |

`Rejected` 는 `isRetryable = false` — 재제출이 전면 거부라 같은 사진으로는 결과가 같다. **재촬영만 열어 둔다.**

#### 🔴 응답 유실 회복 절차 (계약 §3 요구사항)

```
POST §3 → Unreachable
        → GET §4 로 내 status 확인 (내 userId 는 UserInfoRepository, ChallengeDetailViewModel 선례)
            · VERIFIED → 이미 성공. 완료 처리하고 재제출하지 않는다
            · PENDING  → 반영 안 됨. 재시도 가능한 실패 표시
```

🔴 **거부 문구를 성공으로 해석하는 코드는 0건**이다(계약 명시 금지). 같은 700 이 *"진짜로 이미 인증한
상태"* 에서도 나오므로 문구 매칭은 틀린다. **테스트로 고정했다**:
`이미 인증을 완료했어요 거부 문구가 와도 성공으로 해석하지 않는다`.

`GET §4` 는 상태 조건이 없음을 backend-dev 가 서버 코드로 확인했고 계약에 *"회복 절차의 전제다.
바꾸지 마라"* 로 명문화됐다 — 회복 절차가 705 에 갇히지 않는다.

#### 🔴 개편 중 발견한 함정 — 이게 없었으면 실기에서 깨졌다

사용자 지시 *"기본 인증 클라이언트 사용"* 을 문자 그대로 따르면 **실패한다.**
`KtorfitModule.provideHttpClient` 의 `DefaultRequest` 가 `Content-Type: application/json` 을 **전역으로**
싣는데, **Ktor 는 요청 헤더의 Content-Type 을 body(OutgoingContent)의 contentType 보다 우선**한다.
그대로면 **multipart 의 `boundary` 가 헤더에서 사라져 서버가 파싱하지 못한다**(`사진을 첨부해주세요` 700).

2겹으로 막았다:
1. `DefaultRequest` 를 `headers.appendIfNameAbsent(...)` 로 교체 — 요청이 스스로 정했으면 기본값을 안 덧붙인다
2. Ktorfit 메서드에 `@Header("Content-Type")` 파라미터를 두고 `MultiPartFormDataContent.contentType`(boundary 포함) 명시 전달

**회귀 테스트로 규약을 고정했다** — `submitVerification 실요청 - DefaultRequest 의 JSON 기본값이
multipart 를 덮지 않는다`. MockEngine + **실제 Ktorfit** + 운영과 동일한 `DefaultRequest` 를 건 채로 검증한다.

> ⚠️ **`DefaultRequest` 는 전 엔드포인트 공용 설정이다.** 기존 JSON 엔드포인트는 스스로 Content-Type 을
> 정하지 않아 동작이 같고 회귀도 전부 통과했지만, **공용 변경이라는 사실은 리뷰 시 인지해야 한다.**

##### 🔴 후속 — 서버 실측 결과 이 함정의 대가는 예상보다 컸다 (2026-08-18, backend-dev)

내가 넘긴 숙제를 backend-dev 가 spring-web 6.2.7 바이트코드로 추적한 결과, **boundary 누락 요청은
`code=700` 이 아니라 HTTP 500 을 받고 있었다:**

```
boundary 누락 → Tomcat InvalidContentTypeException
  → StandardMultipartHttpServletRequest.handleParseFailure()
      메시지에 "exceed" 가 없어 MaxUploadSizeExceededException 이 아닌 MultipartException
  → 기존 핸들러 3종(MaxUploadSizeExceeded/MissingServletRequestPart/HttpMediaTypeNotSupported) 전부 미포착
  → handleUncaught → HTTP 500 "서버 오류가 발생했습니다"
```

🔴 **즉 앱이 2겹 방어를 하지 않았다면 `사진을 첨부해주세요`(700)가 아니라 500 을 봤을 것이다.**
"서버 오류"로 읽혀 **원인이 클라이언트 헤더에 있다는 걸 알아내기 훨씬 어려운 자리**였다.

backend-dev 가 `@ExceptionHandler(MultipartException::class)` → `code=700` `요청 형식이 올바르지 않습니다`
를 추가했고, 용량 초과 문구가 가려지지 않는지(하위 타입 우선순위)를 `ExceptionHandlerMethodResolver`
**디스패치 선택 테스트**로 고정했다. 서버 **326/326 passed**. 계약 §3 에도 이 함정이 명시됐다.

🔵 **앱은 아무것도 고칠 필요가 없다** — shape 변경이 없고, 우리 2겹 방어가 애초에 이 경로로 가지 않게 한다.

#### 서빙 전용 클라이언트 — 삭제하지 않고 범위를 좁혔다

`SIGNED_URL_HTTP_CLIENT` → **`PHOTO_SERVING_HTTP_CLIENT`**, `provideSignedUrlHttpClient` →
`providePhotoServingHttpClient`. 업로드용으로는 불필요해졌으나 **§5 사진 서빙에는 그대로 필요**하다 —
`Auth(bearer)` 의 `sendWithoutRequest` 가 `/api/v1/photos/...` 에도 JWT 를 선제 주입하기 때문이다.
pm-lead·backend-dev 양쪽이 존치에 동의했다.

> 🟡 **이 provider 는 현재 참조처가 0이다.** 소비자는 T-M4(Coil) 에서 생긴다. 미사용 코드로 오해받아
> 삭제되는 것을 막으려고 **KDoc 에 그 사실을 명시**해 뒀다.

### C. 🔴 업로드 전 EXIF 명시 제거 (위치정보 유출 차단)

**backend-dev 가 발견한 유출 경로**: 서버는 받은 바이트를 **무가공으로 저장·서빙**한다
(`store()` → `writeAtomically`, `serve()` → `readAllBytes`). 즉 앱이 EXIF 를 실어 보내면
**상대가 GPS 좌표를 그대로 받는다.** 이 앱은 즉석 촬영을 강제해 위치가 붙을 확률이 오히려 높고,
상대는 *"내가 아는 사람"* 이지 신뢰 경계 안쪽이 아니다. **pm-lead 가 제거 책임을 앱으로 확정**했다.

#### 실측 — 두 플랫폼 다 재인코딩이라 원래도 GPS 가 실릴 구조는 아니었다

| 플랫폼 | 파이프라인 | EXIF 전달 여부 |
|---|---|---|
| Android | `Bitmap.compress(JPEG)` — **픽셀에서 새로 인코딩** | 원본 EXIF 를 옮겨 적지 않는다 |
| iOS | `UIGraphicsGetImageFromCurrentImageContext()` 로 새로 렌더 후 `UIImageJPEGRepresentation` | 컨텍스트 산출 이미지에 GPS 메타데이터가 없다 |

🔴 **그러나 이건 인코더 동작에 기댄 "원칙"이지 보장이 아니다.** pm-lead 지시대로 **부수 효과에
기대지 않고 명시적 보장으로 바꿨다.**

#### 구현 — 순수 Kotlin JPEG 세그먼트 제거기

`core/camera/src/commonMain/.../JpegMetadata.kt` 신규. `strip()` / `hasMetadataSegment()`.

- **제거**: `APP1`(`FF E1` — Exif/XMP), `APP13`(`FF ED` — IPTC). **GPS 를 담을 수 있는 것들**
- **보존**: `APP0`(JFIF 표준 헤더), `APP2`(ICC 컬러 프로파일 — 지우면 색 재현이 바뀐다)
- **`FF DA`(SOS) 이후는 통째로 보존** — 스캔 데이터에 `FF 00` 스터핑과 마커처럼 보이는 바이트가 있어 파싱하면 안 된다
- 🔴 **JPEG 이 아니거나 파싱 중 범위를 벗어나면 원본을 그대로 반환** — 제거 실패보다 **사용자 사진 파괴가 훨씬 나쁘다**

**플랫폼 인코더에 의존하지 않는 순수 Kotlin 이라 commonTest 로 보장을 고정할 수 있다**는 것이
이 설계의 핵심이다. 양 플랫폼 `PhotoCompressor` 가 최종 바이트를 여기에 통과시킨다.

#### 회전 비의존성 확인 (지시 ③)

- **Android**: `applyExifRotation()` 이 **원본 파일의** EXIF orientation 을 읽어 **픽셀을 돌린다**.
  출력 EXIF 에 의존하지 않는다 → 제거해도 방향이 유지된다
- **iOS**: `drawInRect` 가 방향을 **픽셀에 굽는다** → 동일

**양쪽 KDoc 에 `JpegMetadata.strip` 과의 계약으로 명시**해 뒀다. 회전 로직 자체는 건드리지 않았다.

#### 계측

기존 압축 실측 로그에 `EXIF제거=` 불리언을 **양 플랫폼 동일 형식으로** 추가했다. T-I1 실기 검증 때
사람이 눈으로 확인할 수 있다. 결과 크기·목표 초과 판정도 **제거 후 최종 바이트 기준**으로 바꿨다.

---

### D. 🔴 2차 개정 — 사진 조회도 서명 URL 폐기 → JWT 엔드포인트

**같은 날 두 번째 사용자 결정.** 1차 때 *"조회는 안 바뀐다"* 던 단서가 철회됐다.

```
[전] §4 photoUrl(절대 URL + ?exp=&sig=) + photoUrlExpiresAt(10분)
     §5 GET /api/v1/photos/{cid}/{uid}/{파일명}?exp=&sig=   ← Bearer 금지
[후] §4 photoUrl(상대 경로 "/api/v1/challenges/7/photos/challenger")  ← 만료 필드 제거
     §5 GET /api/v1/challenges/{id}/photos/{party}          ← Bearer 필수
```

#### 🔴 내 판단이 뒤집힌 건 — `PHOTO_SERVING_HTTP_CLIENT` 제거

**1차 때 이 provider 를 존치시킨 게 나였다**(근거: `Auth(bearer)` 의 `sendWithoutRequest` 가 사진 URL 에
우리 JWT 를 주입 → 오브젝트 스토리지 이사 시 남의 호스트로 자격증명이 나간다). backend-dev 도 동의했다.

**그 전제가 소멸했다.** 사진이 우리 JWT 엔드포인트가 되면서 **선제 헤더 주입이 피해야 할 동작이
아니라 정확히 원하는 동작**이 됐다. → `NetworkQualifiers.kt` **파일 삭제**,
`providePhotoServingHttpClient()` **삭제**.

🔵 backend-dev 도 자기 ADR 근거를 정정했다 — *"JWT 엔드포인트로 바꾸면 이미지 로더에 인증 헤더를
심어야 해서 복잡해진다"* 던 전제가 틀렸고, **Coil 3 `coil-network-ktor3` 가 기존 인증 `HttpClient` 를
그대로 받는다.** 전제가 무너지자 서명 URL 에는 순수 비용만 남았다.

> 🔵 **결과적으로 참조처 0인 provider 를 한 사이클 들고 있었던 셈이다.** 다만 1차 시점의 판단은
> 그때 계약(§5 Bearer 금지) 기준으로는 옳았다 — **계약이 바뀌어 근거가 사라진 것**이지 오판이 아니었다.

#### `photoUrlExpiresAt` 제거 — 매퍼의 쌍 규칙이 통째로 사라진다

| 파일 | 변경 |
|---|---|
| `remote/network/.../di/NetworkQualifiers.kt` | **파일 삭제** |
| `remote/network/.../di/KtorfitModule.kt` | `providePhotoServingHttpClient()` + `@Named` import 삭제. 🔴 `sendWithoutRequest` 는 **무변경** |
| `remote/model/.../ChallengeVerificationsResponse.kt` | DTO 필드 삭제 + JSON 예시 교체 |
| `domain/model/.../ChallengeVerifications.kt` | 필드 삭제 + `photoUrl` KDoc 재작성(상대 경로·인증 필요). `partyOf()` 유지 |
| `remote/mapper/.../VerificationMappers.kt` | 🔴 **`urlPairValid` 강등 규칙 삭제** — `photoUrl` 단순 통과 |
| `domain/repository/.../VerificationRepository.kt` | `getVerifications` KDoc 의 *"읽기 URL 만료 시 재조회"* 서술 정정 |
| 테스트 4파일 | 픽스처 상대 경로화 · 만료 인자 제거 · wire JSON 교체 |

🔴 **매퍼의 쌍 유효성 규칙**(`photoUrl != null && photoUrlExpiresAt != null` 이 아니면 둘 다 null 로 강등)이
**존재 근거를 잃었다.** 만료가 없으니 쌍이 없다. 그 규칙만을 고정하던 테스트 3건도 함께 삭제했다.

🔵 **회복 절차는 무변경**이다 — `partyOf(myUserId)?.status` 만 읽고 `photoUrl`·만료를 보지 않는다.
관련 테스트 5건 전부 무수정 통과했다. **만료가 사라져도 회복 절차가 흔들리지 않는 설계였다.**

#### ⚠️ T-M4 로 넘기는 실측 — `photoUrl` 이 **상대 경로**다

backend-dev 가 *"앱에서 상대 경로가 곤란하면 회신해 달라"* 고 물었다. **곤란하지 않다 — 상대 경로가 맞다.**
서버가 절대 URL 을 만들려면 host 를 알아야 하는데 **Android 에뮬레이터는 `10.0.2.2`, iOS 시뮬레이터는
`localhost`** 로 같은 서버에 닿는다. 절대 URL 로 돌리면 그 문제가 되살아난다.

##### 🔴 조인은 "확정할 것"이 아니라 **"고쳐야 할 것"이다** — 내 가정이 틀렸다

`BuildKonfig.BASE_URL` 은 **trailing slash 로 끝나고**(`http://172.30.1.102:8080/`) `photoUrl` 은
**`/` 로 시작**한다. 단순 접합하면 `//` 가 생긴다:

```
http://172.30.1.102:8080//api/v1/challenges/7/photos/challenger
```

🔴 **나는 처음에 *"대개 서버가 관용한다"* 고 적었다. 틀렸다.** backend-dev 가 MockMvc 로 실측했다:

| 요청 경로 | status | 핸들러 도달 |
|---|---|---|
| `/api/v1/challenges/7/photos/challenger` | 200 | ✅ |
| `//api/v1/challenges/7/photos/challenger` | 🔴 **404** | ❌ **도달 못 함** |
| `/api/v1//challenges/7/photos/challenger` | 🔴 **404** | ❌ **도달 못 함** |

Spring Security `StrictHttpFirewall` 은 `.`/`..` 만 막고 빈 세그먼트는 통과시키지만, **Spring MVC 의
`PathPatternParser`(Boot 3 기본값)가 빈 세그먼트를 관용하지 않는다.** 앞이든 중간이든 겹치면 404 다.

##### 🔴 진짜 위험 — 이 404 는 **조용하다**

§5 는 *"상대가 아직 인증 안 함"* 도 **404** 로 답한다. 즉 **조인 버그 404 와 정상 404 가 앱에서
구분되지 않는다.**

> **증상**: 사진이 영원히 안 보이는데 앱은 *"상대가 아직 인증 안 했나 보다"* 로 읽는다.
> **에러도 안 뜨고 로그도 안 남는다.**

두 404 는 응답 모양이 다르지만(조인 버그는 `BaseResponse` JSON 바디 + `Cache-Control` 없음 / 정상은
바디 없음 + `no-store`) 🔴 **그걸로 분기하면 안 된다** — 라우팅 404 의 바디 모양은 계약이 아니라
프레임워크 사정이다. **조인을 정확히 하는 것이 유일한 답이다.**

##### 🔴 왜 이 실수가 나기 쉬운가 — 레포 관행과 정반대다

**기존 레포는 `baseUrl`(trailing slash) + 경로(leading slash 없음)** 관행이다:

```kotlin
"${BuildKonfig.BASE_URL}api/v1/auth/refresh"          // KtorfitModule — 앞에 / 없음
@POST("api/v1/challenges/{id}/verification")           // Ktorfit 선언 — 앞에 / 없음
```

**그런데 `photoUrl` 은 서버가 leading slash 를 붙여 내려준다.** 관행대로 `"${BASE_URL}$photoUrl"` 을
쓰면 **100% `//`** 가 된다. **관행을 따르는 것이 곧 버그가 되는 자리**다.

##### T-M4 처방

- `baseUrl.trimEnd('/') + photoUrl` 로 조인하고 **조인 지점을 한 곳으로 모을 것**
  (Ktor `URLBuilder` / `Url(baseUrl).resolve(path)` 도 정규화해 주지만 어느 쪽이든 한 곳이어야 한다)
- 🔴 **조인 결과를 테스트 1건으로 고정할 것** — 그 문자열이 곧 **Coil 캐시 키**다
- **서버는 `//` 를 관용하도록 고치지 않는다**(backend-dev 판정): 흡수하면 잘못된 URL 이 정상처럼 동작해
  버그가 숨고, 같은 사진에 **캐시 키가 두 개**(`/api/...` vs `//api/...`) 생긴다

✅ **현재 라이브 버그는 없다** — `photoUrl` 소비자가 0건이라 조인 코드가 아직 존재하지 않는다.
**T-M4 에서 배선하는 순간 재현되므로 착수 시점의 첫 항목으로 둔다.**

#### 정리된 계획 (실코드 아님)

- 캐시 키에서 `exp`/`sig` 쿼리를 떼어내는 처리 → **불필요.** 경로에 쿼리가 없어 **경로가 곧 캐시 키**다
- 만료 감지 → §4 재조회 분기 → **개념 자체가 소멸.** 실코드 분기는 애초에 없었다(소비자 미존재)
- 🔴 **T-M4 가 새로 져야 할 책임**: `404` 를 캐시하지 않을 것. 같은 URL 이 **404 → 200 으로 바뀌는 자리**라
  (상대가 아직 인증 안 함) 404 를 캐시하면 **상대가 인증한 뒤에도 사진이 안 보인다.** 서버가
  `no-store` 로 강제하지만 **앱 캐시 계층에서도 확인**해야 한다 — 서명 URL 시절에는 URL 이 매번 달라져
  생길 수 없던 문제다

---

## 📊 2026-08-18 테스트 실측

🔴 **XML 직접 read.** timestamp 는 UTC(KST = +9h). **baseline 을 먼저 떠 stale 을 배제**했다.

### multipart 개편 검증 — `BUILD SUCCESSFUL in 1m 32s`

XML mtime 전부 `8 18 16:13`. baseline 은 datasource/mapper `8/14 11:01`, network `8/14 10:35`,
verify/detail `8/18 10:35`, main `8/14 10:42` 로 **전부 이전** → stale 아님.

| 모듈 | tests | failures | errors |
|---|---|---|---|
| `remote:datasource` (3 클래스) | 30 | 0 | 0 |
| `remote:mapper` (8 클래스) | 71 | 0 | 0 |
| `remote:network` | 7 | 0 | 0 |
| `feature:challenge:verify` | 25 | 0 | 0 |
| `feature:challenge:detail` | 16 | 0 | 0 |
| `feature:main` | 10 | 0 | 0 |
| **소계** | **159** | **0** | **0** |

`:composeApp:compileDebugKotlinAndroid` 통과 — **DI 시그니처가 3레이어 바뀌었으므로 Koin KSP 배선의 실질 검증**이다.

### EXIF 제거 검증 — `BUILD SUCCESSFUL in 33s`

XML mtime `8 18 16:25`, timestamp `2026-08-18T07:25:11Z`. baseline `8/14 10:33` → stale 아님.

| 클래스 | tests | failures | errors |
|---|---|---|---|
| `JpegMetadataTest` (신규) | **10** | 0 | 0 |
| `PhotoScalingTest` | 13 | 0 | 0 |
| `CompressionSpecTest` | 5 | 0 | 0 |
| **`:core:camera` 소계** | **28** | **0** | **0** |

**누적 187/187 passed** (159 + `:core:camera` 28).

### 계약 금지사항·경계 케이스를 고정한 테스트 (XML testcase 목록에서 실행 확인)

| 테스트 | 무엇을 막는가 |
|---|---|
| `이미 인증을 완료했어요 거부 문구가 와도 성공으로 해석하지 않는다` | 계약이 **명시 금지**한 문구 매칭 |
| `Unreachable 이어도 조회된 내 상태가 VERIFIED 면 재제출 없이 완료로 전이한다` | 회복 절차의 핵심 동작 |
| `submitVerification HttpError 500 - Rejected 가 아니라 Unreachable` | "모름"을 거부로 오분류 |
| `submitVerification 실요청 - DefaultRequest 의 JSON 기본값이 multipart 를 덮지 않는다` | boundary 유실 |
| 🔴 `GPS 페이로드가 결과에 남지 않는다` | **위치정보 유출** |
| `SOS 이후 스캔 데이터는 마커처럼 보이는 바이트가 있어도 그대로 보존된다` | 사진 손상 |
| `JPEG 이 아닌 입력은 원본 그대로 반환된다` · `잘린 JPEG 은 원본 그대로 반환된다` | 사진 파괴 |

### 구 계약 심볼 잔존 — **0건**

`upload-url` · `issueUploadUrl` · `issueUploadTarget` · `photoKey` · `PhotoUploadResult` ·
`VerificationUploadTarget` · `uploadPhoto` · `SIGNED_URL_HTTP_CLIENT` 전수 grep.
유일한 출현은 `VerificationRepository` KDoc 의 *"photoKey 개념은 앱에 존재하지 않는다"* 다.

### 2차 개정(서명 URL 폐기) 검증 — `BUILD SUCCESSFUL in 1m 33s`

XML mtime 전부 **`8/18 17:07~17:08`**. baseline 은 mapper/datasource/network/detail `8/18 16:13`,
verify `8/18 16:25` 로 **전부 이전** → stale 아님.

| 모듈 | tests | failures | errors |
|---|---|---|---|
| `remote:mapper` | **69** | 0 | 0 |
| `remote:datasource` | 30 | 0 | 0 |
| `remote:network` | 7 | 0 | 0 |
| `feature:challenge:verify` | 25 | 0 | 0 |
| `feature:challenge:detail` | 16 | 0 | 0 |
| `data:repositoryImpl` | 14 | 0 | 0 |
| **JVM 소계** | **161** | **0** | **0** |
| `feature:challenge:verify` **iOS** | **25** | 0 | 0 | `2026-08-18T08:08:01.886Z` |

`:composeApp` **Android·iOS 양쪽 컴파일 통과.**

🔵 **`remote:mapper` 가 71 → 69 로 줄어든 것은 정상이다** — 쌍 규칙 소멸로 3건을 지우고
ADR-0010 커버리지 보전용 1건(`verifiedAt 이 ISO 로 오면 그 값만 null`)을 추가해 **-3 +1 = -2** 다.

🔴 **회복 절차 테스트 5건은 무수정으로 통과했다** — 만료 제거가 회복 절차를 건드리지 않는다는
설계 가정이 실측으로 확인됐다.

### ✅ iOS 검증 — `BUILD SUCCESSFUL in 54s`, 컴파일 에러 0

`:core:camera:compileKotlinIosSimulatorArm64` · `:remote:datasource:compileKotlinIosSimulatorArm64` ·
`:composeApp:compileKotlinIosSimulatorArm64` + 테스트 3종.

🔴 **stale 배제**: 아래 표는 **이번 실행에서 갱신된 XML 만** 담았다. `core:push`(9) ·
`feature:main`(9) 의 iOS XML 은 **2026-08-08 자로 이번 실행 대상이 아니다 — 합산하지 않았다.**

| 모듈 | 클래스 | tests | failures | errors | XML timestamp | baseline |
|---|---|---|---|---|---|---|
| `core:camera` | `JpegMetadataTest` | **10** | 0 | 0 | `2026-08-18T07:31:26.873Z` | 없음(신규) |
| `core:camera` | `PhotoScalingTest` | 13 | 0 | 0 | `2026-08-18T07:31:26.878Z` | `8/14 10:33` |
| `core:camera` | `CompressionSpecTest` | 5 | 0 | 0 | `2026-08-18T07:31:26.851Z` | `8/14 10:33` |
| `feature:challenge:verify` | `VerifyViewModelTest` | **25** | 0 | 0 | `2026-08-18T07:34:30.878Z` | **없음 — iOS 최초 실행** |
| `feature:challenge:detail` | `ChallengeDetailViewModelTest` | **16** | 0 | 0 | `2026-08-18T07:34:38.635Z` | **없음 — iOS 최초 실행** |
| **iOS 합계** | | **69** | **0** | **0** | (mtime 전부 `8/18 16:31~16:34`) | |

🔵 **`PhotoCompressor.ios.kt` 가 편집됐고 `JpegMetadata` 가 iOS 타겟에서도 통과**한다 —
순수 Kotlin 이라 양 플랫폼에서 같은 보장이 성립함을 실측으로 확인했다.
🔵 **`:composeApp` iOS 컴파일 통과**는 개편된 DI·시그니처가 iOS 소스셋에서도 맞는다는 뜻이다.

#### 🔴 이 과정에서 드러난 **기존 결함** — `:remote:datasource` 등 3개 모듈의 iOS 테스트가 돈 적이 없다

첫 시도는 **BUILD FAILED** 였다. 원인은 **Kotlin/Native 가 백틱 함수명에 `,` `(` `)` 를 금지**하는데
(JVM 은 허용) 레포 곳곳의 테스트 이름이 이를 위반하고 있었기 때문이다:

| 파일 | 위반 | 출처 |
|---|---|---|
| `ChallengeRemoteDataSourceImplTest.kt` | 7 | 🔵 **기존**(마지막 커밋 `101a4f9`, 2026-08-06) |
| `LoginRemoteDataSourceImplTest.kt` | 6 | 🔵 **기존** |
| `UserInfoRepositoryImplTest.kt` | 5 | 🔵 **기존** |
| `FcmTokenRepositoryImplTest.kt` | 3 | 🔵 **기존** |
| `WireFormatBaselineTest.kt` | 1 | 🔵 **기존** |
| `VerificationRemoteDataSourceImplTest.kt` | **1** | 🔴 **내가 만든 것 — 고쳤다** |

**내 것 1건은 수정했다** (`onError 호출, onSuccess 미호출` → `onError 호출하고 onSuccess 미호출`).
child 가 **기존 파일의 명명 관행을 그대로 따라** 생긴 것이다.

🔴 **나머지 22건은 기존 결함이고 건드리지 않았다**(범위 밖, tracked·무수정 파일). 그 결과
**`:remote:datasource` · `:data:repositoryImpl` · `:core:utils` 의 commonTest 는 iOS 타겟에서
한 번도 컴파일된 적이 없다.** baseline 스캔이 이를 뒷받침한다 — iOS 테스트 XML 이 존재하던 모듈은
`core:push` · `feature:main` · `core:camera` **셋뿐이고, 그 셋에는 위반이 0건**이다.

**영향**: 이 세 모듈의 단위 테스트는 **JVM 에서만 검증되고 있다.** KMP 프로젝트로서 실질적인 커버리지
구멍이며, 이름 22개를 고치면 열린다. **백로그 후보로 pm-lead 에 보고했다.**
(그래서 이번 실행에서는 `:remote:datasource` 는 **main 소스셋 컴파일만** 돌려 개편한 프로덕션 코드의
iOS 정합성은 확인하고, 기존에 깨져 있던 commonTest 만 제외했다.)

---

## 🔴 2026-08-24 — T-M4 1단계 (디자인 비의존 구간)

사용자 결정으로 T-M4 범위가 **상세 화면 재구성**까지 확장됐다(spec §4 개정). pm-lead 지시대로
**디자인 비의존 구간부터** 착수했다 — UI 재구성(VS 헤더·미션 카드 분리·사진 표시)은 design.md 대기.

> 🔵 **선행 확인**: 사용자가 `74e2f74` 로 **이전 작업분을 전부 커밋**했고 상세 모듈이 재구성됐다
> (`component/ChallengeDetailContract.kt` → `screen/ChallengeDetailScreen.kt` 통합). **내 인증 CTA 는
> 그 리팩터링에서 살아남았고**, 현재 구조 위에서 작업했다.

### A. `photoUrl` 조인 — 한 곳으로 모으고 테스트로 고정

🔴 **조용한 404 를 막는 유일한 방지선**이다(mobile-report 16번). 매퍼에 조인을 도입했다:

```kotlin
// :remote:mapper — BuildKonfig 를 import 하지 않는다. baseUrl 은 파라미터로 받아 순수하게 유지
internal fun joinPhotoUrl(baseUrl: String, path: String?): String? =
    path?.let { baseUrl.trimEnd('/') + "/" + it.trimStart('/') }
```

**양쪽을 다 다듬는다** — 한쪽만 다듬으면 반대 형태가 오는 순간 깨진다. `toChallengeVerifications(baseUrl)`
로 시그니처를 바꾸고 `VerificationRemoteDataSourceImpl` 이 `BuildKonfig.BASE_URL` 을 주입한다.
도메인 `photoUrl` 은 이제 **절대 URL** 이며 KDoc 을 그에 맞게 정정했다.

**조인 테스트 6건 추가** — 겹침/한쪽만 있음/양쪽 없음/`//` 부재(스킴 제외)/null/매퍼 통과.

> ⚠️ **막힌 지점 1건**: `BuildKonfig` 가 **`internal`** 이라 `:remote:datasource` 에서 안 보였다.
> `remote/network/build.gradle.kts` 에 `exposeObjectWithName = "BuildKonfig"` 한 줄을 추가해 풀었다
> (이름 변화 없이 public 으로만 전환 — 플러그인 소스 확인). **빌드 파일 변경이므로 리뷰 시 인지 필요.**

### B. §4 조회 연동 + 인증 버튼 게이트

`ChallengeDetailViewModel` 에 `VerificationRepository` 를 주입해 상세 조회 후 인증 현황을 함께 받는다.
`Data` 에 `verifications: VerificationSection?`(내/상대 status + photoUrl, **'나/상대' 관점으로 확정**) 추가.

```kotlin
canVerify = status == STATUS_IN_PROGRESS && verifications?.myStatus != VerificationStatus.VERIFIED
```

🔴 **기존 한계가 해소됐다** — 이미 인증한 사용자에게 CTA 가 더 이상 보이지 않는다.

#### 🔴 부분 실패 정책 — 이 작업의 핵심 판단

인증 현황 조회가 실패하거나 **관점 미상**(내 userId 를 못 얻음)이면 `verifications = null` 이고,
`canVerify` 는 **"노출" 쪽으로 폴백**한다.

- **숨기면**: 아직 인증하지 않은 사용자가 **일시적 네트워크 오류 때문에 인증 자체를 못 하게 된다** — 주 액션이 막힌다
- **노출하면**: 최악이 이미 인증한 사용자가 700 을 받는 것이고, 이는 서버가 정확히 답하는 기존 경로다
- → **막는 실패보다 중복 시도 실패가 낫다.** 화면도 `Error` 로 떨어뜨리지 않는다 — 계약서는 이미 받았고 그것만으로 화면이 성립한다

🔵 **child 판단 2건을 승인했다**: ① 두 조회를 마친 뒤 **한 번에** `Data` 로 전이한다 — 2단계로 갱신하면
`canVerify` 가 `true → false` 로 뒤집혀 **이미 인증한 사용자의 손가락 아래에서 CTA 가 사라진다**.
대가는 Loading 이 조회 1회만큼 길어지는 것. ② 관점 미상이면 `getVerifications` 를 아예 부르지 않는다
(받아도 '나/상대' 로 세울 수 없어 버릴 값).

### C. Coil 배선 — 이 앱의 첫 원격 이미지

`composeApp` 에 `coil-compose` + `coil-network-ktor3`(3.2.0) 추가. `App.kt` 에 공용 루트
`ChallengeApp(content)` 을 신설해 `setSingletonImageLoaderFactory` 로 싱글턴을 배선하고,
Android `MainActivity` / iOS `MainViewController` 가 이를 감싼다.

🔴 **앱의 기본 인증 `HttpClient` 를 Koin 에서 받아 그대로 물린다** — 사진이 우리 서버의 JWT 보호
경로라 Bearer 가 필요하고, `Auth(bearer)` 가 **401 시 토큰 갱신 후 재시도**까지 해 준다. 전용
클라이언트를 새로 만들면 그 이득을 잃는다. **예전 서명 URL 계약 때 있던 전용 클라이언트를 되살리지
말 것**을 주석으로 못 박았다.

#### 🔴 `respectCacheHeaders` 는 **Coil 3 에 없다** — 내 지시가 틀렸다

내가 *"기본값 true 이니 끄지 마라"* 로 지시했는데 **그건 Coil 2(OkHttp) API** 다. child 가 3.2.0
원본 소스를 대조해 정정했다. Coil 3 의 디스크 캐시 정책은 `CacheStrategy` 로 옮겨졌고 기본
`DefaultCacheStrategy` 는 오히려 **캐시 헤더를 존중하지 않는다.**

🔵 **그럼에도 404 캐시 문제는 발생하지 않는다** — `NetworkFetcher` 가 **2xx·304 가 아니면
`HttpException` 을 던지는 지점이 디스크 캐시 기록보다 앞**이라 오류 응답이 애초에 저장되지 않는다.
서버의 `no-store` 와 무관하게 성립한다. **이 성질에 기대고 있다는 사실**과 *"오류 응답까지 저장하는
커스텀 `CacheStrategy` 를 성능 이유로 끼워 넣지 말 것"* 을 주석으로 남겼다.

> ⚠️ **검증 수준을 정직하게 밝힌다**: 위는 **3.2.0 소스 대조**로 확인한 것이지 **런타임 실측이 아니다.**
> 404→200 전이 실측은 사진 UI 가 붙은 뒤(또는 T-I1 실기)에 가능하다. **미해결 18번**으로 등재했다.
> 200 응답의 `max-age`/재검증까지 서버 헤더대로 따르려면 `coil-network-cache-control` 아티팩트가
> 별도로 필요하다(카탈로그에 없고 `@ExperimentalCoilApi`) — 이번 범위 밖.

### 그 외 실측 정정 3건 (child)

- `libs.coil.compose` 는 **없다.** 카탈로그 alias 가 `coil` 이다(`libs.coil`)
- `libs.ktor.client.core` 를 `composeApp` 에 **명시 추가**해야 했다 — `:remote:network` 가 `implementation` 이라 전이되지 않는데 `App.kt` 가 `HttpClient` 타입을 직접 참조한다
- `App.kt` 에 **루트 Composable 이 없었다** — 실제 루트가 플랫폼마다 따로였다(`MainActivity` / `MainViewController`). 공용 루트를 신설하고 양쪽이 감싸게 했다

### 📊 T-M4 1단계 테스트 실측

`BUILD SUCCESSFUL`, 컴파일 에러 0. **`:composeApp` Android·iOS 양쪽 컴파일 통과**(Coil 배선 포함).

| 모듈 | tests | fail | err | XML mtime |
|---|---|---|---|---|
| `remote:mapper` | **75** | 0 | 0 | `08/24 23:28` |
| `remote:datasource` | 30 | 0 | 0 | `08/24 23:28` |
| `remote:network` | 7 | 0 | 0 | `08/24 23:42` |
| `feature:challenge:detail` | **25** | 0 | 0 | `08/24 23:35` |
| `feature:challenge:verify` | 25 | 0 | 0 | `08/24 23:42` |
| `data:repositoryImpl` | 14 | 0 | 0 | `08/24 23:42` |
| `feature:main` | 10 | 0 | 0 | `08/24 23:42` |
| `core:camera` | 28 | 0 | 0 | ⚠️ `08/18 16:25` |
| **합계** | **214** | **0** | **0** | |

⚠️ **`core:camera` 는 이번에 재실행되지 않았다** — 모듈이 무변경이라 Gradle 이 UP-TO-DATE 로 건너뛰었다.
숫자는 8/18 실행분이며 **이번 세션의 fresh 결과가 아니다.** 나머지 7개 모듈은 전부 `08/24` 로 fresh.

증가분: `remote:mapper` 69 → **75**(조인 테스트 6건), `feature:challenge:detail` 16 → **25**(게이트·폴백·관점 9건).

**iOS**: `feature:challenge:detail` **25/25** (`2026-08-24T14:35:33.697Z`) 통과.

---

## 🔴 2026-08-25 — T-M4 2단계 (UI 재구성, design.md 정본)

design.md 도착 후 상세 화면을 재구성했다. **`BUILD SUCCESSFUL`, 컴파일 에러 0, Android·iOS 양쪽 통과.**

### 만든 것

| 구분 | 산출물 |
|---|---|
| `:core:utils` | **`deadlineAbsoluteText(challengeDate, deadline)`** — 절대 마감 `"8/3 24:00"` |
| `:core:ui` | **`VerificationStatusPill`** — 홈 `StatusPill`+`statusVisualOf()` 승격. 도메인 `VerificationStatus` 를 직접 받는다 |
| `detail/component/` | **`VsHeaderCard`** · **`MissionCard`**(1종, 하단 슬롯) · **`VerificationPhoto`**(160dp 고정) · **`OathSummaryCard`** |
| `detail/contract/` | `DeadlineDisplay.kt` — 표기 문자열 + `DeadlineTone` |

### 🔴 하루 밀림 — 테스트로 고정했다

`deadline` 은 **익일 00:00 배타적 끝점**이라(`challengeDate: 8/3` + `deadline: 8/4 00:00`) 그대로 찍으면
`8/4` 가 나오는데 **정답은 `8/3 24:00`** 이다. `challengeDate` 우선 + `deadline` 폴백(00:00 이면 전날 24:00)
으로 구현하고 **경계 7건**(월 경계 `9/1→8/31`, 연 경계 `1/1→12/31`, 0패딩, 비-자정 폴백 등)을 고정했다.

🔵 **마감 행은 design.md 에서 Lovable 을 의도적으로 벗어나는 유일한 지점**이다 — VS 헤더의 상대 표기
(`3시간`)만으로는 *"오늘 자정인지 내일인지"* 를 복원할 수 없고 그건 계약 조건이다. **코드 주석에 근거를
남겼다** — 안 남기면 다음 사람이 "디자인에 없는 행"으로 지운다.

### 🔴 분 단위 티커 — 기존 주석과 정면으로 부딪히던 지점

기존 주석은 *"시계는 매핑 시점 1회만 읽는다"* 였다. **그 주석이 막으려던 건 갱신이 아니라 Composable
안에서의 시계 읽기**이므로, ViewModel 이 1분 주기로 state 를 방출하는 방식으로 구현하고 **주석을 새
동작에 맞게 다시 썼다**(원래 의도인 "시계 읽기 지점을 ViewModel 로 고정"은 보존).

- 마감을 넘긴 회차까지 반영(URGENT → NEUTRAL) 후 루프 종료 — 이후엔 바뀔 게 없다
- `retry()` 시 이전 티커를 취소(두 루프가 같은 state 를 갱신하는 것 방지)
- **중복 방출을 명시적으로 걸렀다** — `StateFlow` 의 equals 흡수에 기대지 않는다. `Data` 에 구조적 동등성이
  깨지는 필드가 하나만 붙어도 흡수가 조용히 풀려 매분 전체 recomposition 이 시작되기 때문

### 홈 회귀 — 0건

`VerificationStatusPill` 승격은 **교체** 방식(중복 아님)을 골랐다. 시각 값(radius 10dp·아이콘 12dp·
패딩 8×4·alpha 0.10·`medium10`)을 현행 홈과 **완전 동일**하게 옮겼고 호출 지점이 1곳뿐이라 위험이 낮다고
판단했다. 홈 표시 전용 enum `ChallengeVerificationStatus` 는 존재 이유(*":core:designsystem 은 도메인에
의존하지 않는다"*)가 `:core:ui` 에선 성립하지 않아 **삭제**했다. **홈 테스트 20/20 그대로 통과.**

### ⚠️ 관측·한계 3건

1. 🔴 **티커 테스트를 만들지 않았다.** `nowKst()` 가 실제 시계를 직접 읽는데 `runTest` 의 `advanceTimeBy` 는
   `delay` 만 건너뛰고 `Clock.System` 을 움직이지 못한다. 몇 분을 진행시켜도 티커가 만드는 문자열이 직전과
   같아 **통과해도 "갱신됨"을 증명하지 못하는 테스트**가 된다. 검증하려면 ViewModel 에 시계를 주입해야 하고
   그건 Koin KSP 생성자 구조를 건드린다. **조작된 통과보다 정직한 미검증을 택했고** 테스트 파일에 주석으로
   남겼다. → 미해결 20번
2. ⚠️ **긴 미션 + 큰 폰트에서 CTA 위치는 산술 추정이지 렌더 관측이 아니다**(빌드 없이 프리뷰를 띄울 수 없다).
   추정으로는 360×800dp/fontScale 1.5 에서 CTA 하단이 ~493dp 라 여유가 있고, **360×640dp 소형 기기에서
   여유 ~67dp 로 아슬하다.** fontScale 2.0 + 긴 문구면 소형 기기에서 **첫 화면 밖으로 밀린다.**
   🔵 부수 발견: `IconTextButton` 은 `height = 52.dp` **하드 고정**이라 폰트 스케일을 따라 커지지 않고,
   2.0x 에서 `bold16` lineHeight(48dp)가 그 안에서 클리핑 직전이다. → 미해결 21번
3. **KMP `@Preview` 에는 `fontScale` 파라미터가 없다**(아티팩트 확인). `LocalDensity` 를 갈아 끼우는
   프리뷰 컨테이너로 대체했다.

### 인증 현황 모름일 때 — 뱃지를 뺐다

`verifications == null`(조회 실패·관점 미상)이면 **뱃지를 통째로 렌더하지 않는다.** 뱃지 값이
대기중/인증완료/실패 3종뿐이라 '모름'을 표현할 값이 없고, "대기중"으로 채우면 **이미 인증한 사람을
미인증으로 못 박는 거짓**이 된다 — `canVerify` 가 노출로 폴백하는 이유(단정하지 않는다)와 어긋난다.
라벨만 남기면 아무 주장도 하지 않는다. 사진 영역은 `"인증 현황을 불러오지 못했어요"` + 재시도.

⚠️ **재시도는 기존 `onRetry`(전체 재조회)를 재사용**했다 — 인증현황 전용 재조회가 VM 에 없다. 대가는
화면이 Loading 으로 되감겨 읽던 계약서가 잠깐 사라지는 것이고, 대안이 "뒤로 나갔다 재진입"(같은 전체
재조회를 손으로 하는 것)뿐이라 버튼을 주는 쪽이 낫다고 봤다. `onRetry` KDoc 에 이 대가를 적었다.

### 📊 T-M4 2단계 테스트

| 모듈 | tests | fail | err | mtime |
|---|---|---|---|---|
| `feature:challenge:detail` (JVM) | **29** | 0 | 0 | `08/25 00:32` |
| `feature:challenge:detail` (**iOS**) | **29** | 0 | 0 | `2026-08-24T15:32:50Z` |
| `feature:home` (회귀) | 20 | 0 | 0 | `08/24 23:51` |
| `core:utils` | **35** (28→35, 포맷터 7) | 0 | 0 | `08/24 23:50` |

`:composeApp` **Android·iOS 양쪽 컴파일 통과.** 신규 마감 테스트 4건이 XML testcase 에 실행 확인됨.

---

## 🔴 2026-08-25 — 실기 버그: 로거가 사진 스트림을 소비했다

**T-I1 실기에서 발견.** 서버는 200 + 정상 JPEG 를 주는데 앱은 *"사진을 불러오지 못했어요"* 를 띄우고,
로그에 **JPEG 바이너리가 통째로 찍혔다.**

### 원인 — 세 결정의 교차점에서 터졌다

`HttpNetworkLogger.onResponse` 가 **모든 응답에 무조건 `response.bodyAsText()` 를 호출**해 본문을 소비하고 있었다.

```kotlin
val responseBody = response.bodyAsText().take(MAX_BODY_LENGTH)   // ← 27행, 조건 없음
```

| 결정 | 단독으로는 무해 |
|---|---|
| ① 로거가 모든 응답 본문을 읽는다 | Ktorfit JSON 경로는 Ktor 3 의 **기본 body 저장** 덕에 재읽기가 돼 **무증상**이었다 |
| ② 2차 계약 개정 — 사진을 **기본 인증 HttpClient** 로 받는다 | 401 자동 갱신을 얻는 올바른 결정 |
| ③ Coil `ktor3` NetworkFetcher 는 **스트리밍(`execute {}`)으로 읽는다** | `skipSaveBody()` 라 body 가 저장되지 않는다 |

🔴 **셋이 겹치자 로거가 채널을 먼저 비우고 Coil 에는 빈 스트림이 도착**해 디코드가 실패했다.
**②를 하면서 로거까지 따라 붙어 생긴 회귀**이며, 내가 Coil 을 기본 클라이언트에 물릴 때 예견하지 못한 것이다.

### 🔴 "테스트는 초록인데 실기에서 깨진" 계열

이 feature 에서 반복된 그 부류다(EXIF GPS · `boundary` 500 · `//` 404 · ADR-0010 커버리지 이관).
**단위 테스트가 잡을 수 없던 이유**: JSON 경로만 테스트하면 body 저장이 재읽기를 막아 주므로 영원히 통과한다.
**스트리밍 소비자가 같은 클라이언트를 탄다는 조건 자체가 테스트에 없었다.**

### 수정 — 로거가 Content-Type 을 보고 갈라 읽는다

| Content-Type | 처리 |
|---|---|
| `text/*` · `application/json` · `+json` 접미어 | 기존대로 `bodyAsText()` + 5000자 절단 |
| **그 외(이미지 등)** | 🔴 **본문을 읽지 않고** `[binary: image/jpeg, 2052B]` 요약만 기록 |
| 헤더 없음 · 파싱 실패 · `*/*` | **읽지 않는 쪽으로 기운다** — 로그가 덜 자세한 게 스트림 파손보다 낫다 |

🔵 **Coil 전용 클라이언트 분리는 기각**됐다(pm-lead) — 401 자동 갱신을 잃고 2차 개정 취지에 역행한다.
🔵 부수 효과로 로그의 바이너리 스팸도 사라진다.

**why 주석을 남겼다** — *"스트리밍 소비자가 같은 클라이언트를 쓰므로 로거가 먼저 읽으면 빈 스트림이 간다"*.
안 남기면 다음 사람이 *"로그가 부실하다"* 며 무조건 읽기로 되돌린다.

### 🔵 회귀를 실제로 재현하는 테스트를 세웠다

`이미지 응답은 로거를 거친 뒤에도 후속 reader 가 전체 바이트를 읽는다` — MockEngine + 로거를 건 클라이언트에서
**`prepareGet(...).execute { bodyAsChannel().toByteArray() }`** 로 읽어 원본 바이트와 비교한다.

🔴 **이 경로가 실기의 Coil 과 같다**: Ktor 3.3.1 의 `HttpStatement.fetchStreamingResponse()` 가
`skipSaveBody()` 를 호출하고 `SaveBody` 플러그인이 그 attribute 를 보면 저장을 건너뛴다(소스 확인).
**구버전 로거를 넣으면 이 테스트는 빈/부분 배열로 실패한다** — 즉 회귀를 잡는 테스트다.

추가 5건: JSON 재읽기 비회귀 · 바이너리 요약 문자열 · Content-Type 없음 · JSON 본문 로깅 유지 · 판정 함수 단위 테스트.

⚠️ **한계**: ① 최종 로그 라인 조립까지는 커버하지 않는다(Kermit 출력 캡처 대신 본문 생성 함수를 직접 호출 —
`Logger` 의 minSeverity 가 환경에 따라 출력을 삼킨다). ② **구버전 로거로 되돌려 이 테스트가 실제로 실패하는지는
확인하지 않았다**(mutation 검증 미수행) — 근거는 Ktor 소스 대조다. 🔴 **지금 하지 않은 이유는 사용자가 실기
테스트 중이기 때문**이다 — 로거를 잠깐 되돌리는 동안 사용자가 빌드하면 깨진 버전을 받는다. 요청 시 수행 가능.

### ⚠️ 수정 과정에서 자초한 컴파일 오류 1건 — 중첩 주석

child 가 추가한 KDoc 에 `텍스트류(JSON / text/*)` 라고 적었는데, **`text/*)` 안의 `/*` 두 글자가 중첩 블록
주석을 열었다.** Kotlin 은 블록 주석 중첩을 지원하므로 KDoc 끝의 `*/` 가 **안쪽만 닫고 바깥 주석이 파일 끝까지
열린 채**로 남아, 새로 만든 두 함수가 통째로 주석으로 먹혀 `Unresolved reference` 가 났다.

주석 문구를 `텍스트류(JSON 계열, 그리고 모든 text 하위 타입)` 로 바꿔 해소했다(로직 무변경).
🔵 **교훈**: MIME 와일드카드(`text/*`)를 블록 주석 안에 그대로 쓰면 파일이 깨진다. 같은 파일 전수 grep 으로
다른 `/*` 가 없음을 확인했다.

### 📊 검증

| 모듈 | tests | fail | err | mtime |
|---|---|---|---|---|
| `remote:network` | **13** (7→13, 로거 6건) | 0 | 0 | `08/25 09:31` |
| `remote:datasource` | 30 | 0 | 0 | `08/25 09:31` |
| `feature:challenge:detail` | 29 | 0 | 0 | `08/25 00:32`(무변경 UP-TO-DATE) |

`BUILD SUCCESSFUL`, 컴파일 에러 0, `:composeApp` Android 컴파일 통과.

---

## Working tree 상태

- **작업 브랜치**: `main` (현재 체크아웃된 브랜치. 새로 만들지 않았다)
- **변경분(2026-08-18 기준)**:
  - `??` 미추적: `core/camera/`, `feature/challenge/verify/`, verification 도메인·데이터·remote 파일 일체
  - `M` unstaged: `settings.gradle.kts` · `iosApp/iosApp/Info.plist` · `core/navigation/Route.kt` ·
    `feature/main/*` · `remote/network/di/KtorfitModule.kt` · `remote/api/di/ApiModule.kt` ·
    `feature/challenge/detail/*`(5) · `composeApp/*` 등
- **커밋·푸시·PR 생성 안 함** — 사용자 처리 영역

---

## 미해결 이슈

> 🔄 **2026-08-18 갱신.** 8/14 표의 1·2·3·4 는 해소되거나 재정의됐다. 아래가 현재 상태다.

| # | 항목 | 상태 |
|---|---|---|
| 1 | **T-M3 업로드 + 제출 연동** | ✅ **완료** — multipart 개편본으로 구현. 159/159 |
| 2 | 🔴 **T-M4 상대 사진 보기** | ⏸ **pm-lead 가 범위 밖으로 명시 제외.** 아래 §T-M4 우선순위 권고 참조 |
| 3 | **인증 화면 진입점** | ✅ **완료** — 상세 화면 `IN_PROGRESS` CTA → `Route.Challenge.Verify` |
| 4 | **`PushEvent.OpponentVerified`** | ✅ 해소 — 발송 개시됨(§0.5) |
| 5 | 🔴 **T-M2 실측값** | ❌ 여전히 미측정. 자동 계측 로그(+`EXIF제거=`)가 있고 **T-I1 에서 채운다** |
| 6 | **iOS 촬영 실동작** | ❌ 시뮬레이터에 카메라 없음. **실기기 필요** — T-I1 |
| 7 | 500KB 상한 미보장 | 🟡 목표이지 상한이 아니다. 🔵 **계약이 자동 재압축 루프를 금지**했다(§3) — 도달 자체를 파이프라인 이상 신호로 본다 |
| 8 | core 모듈 생성 스킬 부재 | 🟢 하네스 갭. `scripts/create-core-module.sh` 는 패키지 경로가 `com/lwg/base/*` 로 낡아 쓰지 못했다 |
| 9 | 🔴 **이미지 로더 미배선** | T-M4 의 숨은 선행 작업. Coil 등록만 돼 있고 사용처 0건. 🔵 **2차 개정으로 쉬워졌다** — `coil-network-ktor3` 에 **기본 인증 `HttpClient`** 를 그대로 넘기면 JWT·갱신이 붙는다 |
| 10 | `profileImageUrl` placeholder 전면 활성화 | 🟢 이 feature 범위 밖 — 백로그 후보 |
| 11 | ~~`PHOTO_SERVING_HTTP_CLIENT` 참조처 0~~ | ✅ **소멸.** 2차 개정으로 존재 이유(JWT 외부 유출 방지)가 사라져 **제거**했다. §D 참조 |
| 12 | ⚠️ **`DefaultRequest` 공용 변경** | `appendIfNameAbsent` 로 바꿨다. 전 엔드포인트 공용 설정이므로 리뷰 시 인지 필요. 회귀는 전부 통과 |
| 13 | ✅ **iOS 검증** | **해소.** 컴파일 에러 0, iOS 테스트 **69/69**(camera 28 + verify 25 + detail 16). 2차 개정 후 verify 25 재검증 통과 |
| 14 | 🟡 **EXIF 제거는 앱에만 있다** | 서버는 바이트를 무가공 저장한다. **앱이 아닌 클라이언트가 EXIF 를 실어 보내면 그대로 저장된다** — backend-report 미해결 6번(실사용자 유입 전 재검토)과 같은 항목 |
| 15 | 🔴 **기존 결함 — 3개 모듈 iOS 테스트 미컴파일** | `:remote:datasource`·`:data:repositoryImpl`·`:core:utils` 의 commonTest 가 Kotlin/Native 금지 문자(`,`·`()`)를 쓴 백틱 함수명 **22건** 때문에 iOS 타겟에서 한 번도 컴파일된 적이 없다. **내가 만든 1건은 고쳤고 나머지는 범위 밖**. ✅ **pm-lead 가 백로그 등재 완료** |
| 20 | 🟡 **티커 테스트 부재** | `nowKst()` 가 실제 시계를 읽어 `runTest` 가상 시간으로 갱신을 증명할 수 없다. 검증하려면 ViewModel 에 시계 주입 필요(Koin KSP 생성자 구조 영향). **조작된 통과 대신 미검증을 택했다** |
| 21 | ⚠️ **긴 미션 + 큰 폰트에서 CTA 밀림 가능** | 산술 추정: 360×640dp 소형 기기 + fontScale 2.0 + 긴 문구면 CTA 가 첫 화면 밖. **렌더 관측이 아니다.** 🔵 `IconTextButton` 이 `height=52.dp` 하드 고정이라 폰트 스케일을 안 따르고 2.0x 에서 클리핑 직전 |
| 18 | 🟡 **Coil 404 무캐시 — 런타임 미검증** | 3.2.0 소스 대조로 *"2xx 아니면 디스크 기록 전에 `HttpException`"* 을 확인했으나 **실측이 아니다.** 404→200 전이 확인은 사진 UI 가 붙은 뒤 또는 T-I1 실기에서. `respectCacheHeaders` 는 **Coil 3 에 없다**(Coil 2 API) |
| 19 | ⚠️ **`BuildKonfig` 를 public 으로 전환** | `remote/network/build.gradle.kts` 에 `exposeObjectWithName` 추가. `:remote:datasource` 가 `BASE_URL` 을 보려면 필요했다. **빌드 파일 변경이라 리뷰 시 인지 필요** |
| ~~16~~ | ✅ **`photoUrl` 조인 — 해소** | 매퍼 `joinPhotoUrl` 로 한 곳에 모으고 **테스트 6건으로 고정**. 아래 원문 유지 |
| 16 | 🔴 ~~**`photoUrl` 조인 — T-M4 착수 시 반드시 고칠 것**~~ | **`//` 는 관용되지 않는다. 404 다**(backend-dev MockMvc 실측). 게다가 §5 는 *"상대가 아직 인증 안 함"* 도 404 라 **조인 버그가 정상 상태로 위장돼 조용히 실패한다.** `baseUrl.trimEnd('/') + photoUrl` 로 조인하고 **테스트 1건으로 고정**할 것 — 그 문자열이 곧 Coil 캐시 키다. 상세는 §D |
| 17 | 🔴 **T-M4 는 `404` 를 캐시하면 안 된다** | 같은 URL 이 **404 → 200 으로 바뀌는 자리**다(상대가 아직 인증 안 함). 404 를 캐시하면 상대가 인증한 뒤에도 사진이 안 보인다. 서버가 `no-store` 로 강제하지만 **앱 캐시 계층에서도 확인** 필요 |

---

## 🔴 T-M4 우선순위 권고

**T-M4 는 지시대로 착수하지 않았다.** 다만 **이번 개편으로 그 부재의 체감이 커졌다.**

상세 화면은 *"내가 이미 인증했는지"* 를 모른다(그 정보가 §4 조회에 있고 T-M4 범위다).
따라서 `IN_PROGRESS` 면 CTA 를 **항상** 노출한다. 그런데 재제출 정책이 *"같은 key 멱등"* 에서
🔴 **전면 거부**로 바뀌었다:

```
이미 인증한 사용자 → CTA 노출 → 촬영 → 미리보기 → 제출 → ❌ 700 "이미 인증을 완료했어요"
```

**촬영까지 다 시킨 뒤 거부한다.** 개편 전에는 멱등 성공이라 조용히 지나갔을 경로다.
T-M4 에서 verification 상태로 CTA 를 게이트하면 해소된다. **우선순위 상향을 권고한다.**

---

## API 계약 대비 구현 차이

**없음** (2026-08-18 개정본 기준).

- part 이름 **`photo`** — 계약 §3 문면 확정값 그대로
- 응답 shape — `SubmitVerificationResponse` 무변경 재사용
- 에러 분류 — `code` 기반. **문구 매칭 0건**(계약 명시 금지사항 준수)
- `verifiedAt` **nullable** 유지 (계약 §3 *"nullable 로 잡을 것"*)
- §4 조회·§5 서빙 경로 무변경

🔵 **계약이 앱에 요구한 것 중 이번에 추가로 이행한 것**: 응답 유실 회복 절차(§3),
제출 전 확인 단계 유지(§3 — 촬영→미리보기→확정), EXIF 제거(§3 등재분).
