# VoidMelody Desktop

VoidMelody is a local-first desktop studio for creating text-to-speech audio. It combines a Tauri desktop shell, a Next.js interface, and a FastAPI sidecar that uses the bundled `capcut-tts-api` provider. It is an independent project and is not affiliated with CapCut or ByteDance.

> **Ghi chú tiếng Việt:** Ứng dụng chạy cục bộ trên máy; dữ liệu và tệp âm thanh được lưu trên máy của bạn.

## Architecture

```text
Tauri desktop app
  └─ Next.js UI (apps/web)
       └─ local FastAPI sidecar (apps/api)
            ├─ SQLite data store
            ├─ FFmpeg audio processing
            └─ capcut-tts-api submodule (vendor/capcut-tts-api)
```

The desktop app starts its API sidecar locally and passes a per-launch token to it. No API service is exposed to your network by default.

## Prerequisites

The supported desktop targets are macOS ARM64 (Apple Silicon) and Windows x64.

| Requirement | macOS ARM64 | Windows x64 |
| --- | --- | --- |
| Git | Git 2.30+ | Git for Windows 2.30+ |
| Node and pnpm | Node.js 20+ and Corepack | Node.js 20+ and Corepack |
| JavaScript package manager | `corepack prepare pnpm@10.11.0 --activate` | `corepack prepare pnpm@10.11.0 --activate` |
| Python tooling | Python 3.9+ and [uv](https://docs.astral.sh/uv/) | Python 3.9+ and [uv](https://docs.astral.sh/uv/) |
| Tauri build tooling | Rust stable and Xcode Command Line Tools (`xcode-select --install`) | Rust stable with the MSVC toolchain and Visual Studio 2022 Build Tools (Desktop development with C++, MSVC v143, and a Windows SDK) |
| Runtime tools | `ffmpeg` on `PATH` (for example, `brew install ffmpeg`) | `ffmpeg` on `PATH` (for example, `winget install Gyan.FFmpeg`) and Microsoft Edge WebView2 Runtime |

After installing FFmpeg on Windows, open a new terminal so its `PATH` change is available. The scripts below are identical in PowerShell, Command Prompt, macOS Terminal, and CI; do not use `source`, shell activation commands, or platform-specific path separators.

## Fresh clone, setup, and run

Clone with submodules so the local TTS provider is available:

```bash
git clone --recurse-submodules https://github.com/voidstation-dev/void-melody.git
cd void-melody
corepack prepare pnpm@10.11.0 --activate
pnpm setup:desktop
pnpm dev:desktop
```

`pnpm setup:desktop` installs the pinned JavaScript dependencies, initializes the TTS submodule recursively, synchronizes the API virtual environment with `uv`, builds the API sidecar, and copies FFmpeg and the voice catalog into the desktop bundle inputs.

For an existing clone that was not created recursively, run:

```bash
pnpm setup:vendor
pnpm setup:desktop
```

To develop the browser UI without the desktop shell, run `pnpm dev:web`. To run the API by itself at `http://127.0.0.1:8000`, use:

```bash
pnpm setup:api
pnpm dev:api
```

> **Ghi chú tiếng Việt:** Lần cài đầu tiên cần Internet để tải dependencies. Sau đó, dùng `pnpm dev:desktop` để mở ứng dụng desktop.

## Test and build

Run the API and UI test suites:

```bash
pnpm test:api
pnpm test:web
```

Create a desktop release bundle for the current platform:

```bash
pnpm build:desktop
```

Build artifacts are written below `apps/web/src-tauri/target/release/bundle/`:

| Platform | Typical artifacts |
| --- | --- |
| macOS ARM64 | `dmg/VoidMelody_<version>_aarch64.dmg` and `macos/VoidMelody.app` |
| Windows x64 | `msi/` and `nsis/` installers |

The API sidecar input is generated at `apps/web/src-tauri/bin/melody-api-<target-triple>` (with `.exe` on Windows). These generated files are ignored by Git.

## Release and update workflow

1. Update the desktop version in `apps/web/src-tauri/tauri.conf.json`.
2. From a clean checkout, run `pnpm setup:desktop`, `pnpm test:api`, `pnpm test:web`, and `pnpm build:desktop` on each supported platform.
3. Commit the version change, create a version tag such as `v0.1.1`, and push the tag.
4. The GitHub release workflow checks out submodules recursively, runs the same `pnpm setup:desktop` workflow on macOS, Windows, and Ubuntu, then creates a draft release with platform artifacts. Review and publish that draft in GitHub.

> **Ghi chú tiếng Việt:** Mỗi bản phát hành cần build trên từng hệ điều hành để tạo đúng file cài đặt và sidecar cho nền tảng đó.

## Troubleshooting

### `capcut-tts-api` is empty or missing

Initialize it from the repository root:

```bash
pnpm setup:vendor
git submodule status --recursive
```

If the URL changed, run `git submodule sync --recursive` before `pnpm setup:vendor`.

### FFmpeg cannot be found

Install FFmpeg and confirm the executable is visible in a new terminal:

```bash
ffmpeg -version
pnpm setup:desktop
```

On macOS, `brew install ffmpeg` is the usual installation method. On Windows, `winget install Gyan.FFmpeg` is one option. The setup workflow copies the discovered binary into the desktop bundle inputs.

### Windows build fails because WebView2 or MSVC is missing

Install the Evergreen WebView2 Runtime and Visual Studio 2022 Build Tools with Desktop development with C++, MSVC v143, and a Windows SDK. Restart the terminal, then run `rustup default stable-msvc` and `pnpm setup:desktop` again.

### macOS says the app cannot be opened

Unsigned local builds can be blocked by Gatekeeper. In Finder, Control-click the app, choose **Open**, and confirm the prompt. For a release distribution, sign and notarize the app before publishing.

### Windows SmartScreen warns about the installer

Unsigned installers can trigger SmartScreen. Prefer the release artifact from this repository; for a distributed release, sign the Windows installer with a trusted code-signing certificate.
