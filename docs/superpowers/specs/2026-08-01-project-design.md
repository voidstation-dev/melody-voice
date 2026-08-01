# CapVoice Studio — Design Specification

**Date:** 2026-08-01  
**Project:** CapVoice Studio (Local-first Text-to-Speech Studio)  
**Status:** Approved Specification  

---

## 1. Executive Summary & Context

CapVoice Studio is a desktop/mobile-responsive local-first web application designed for high-quality Vietnamese and multi-language Text-to-Speech (TTS) synthesis. It leverages the reverse-engineered `capcut-tts-api` Python SDK wrapped in a resilient FastAPI backend service, providing an intuitive, professional studio interface built with Next.js 15 App Router, TypeScript, Tailwind CSS, and shadcn/ui.

### 1.1 Target Users & Primary Workflows
- **Content Creators / Podcasters:** Rapidly generate natural Vietnamese audio voiceovers from text scripts, preview voices with zero latency overhead, adjust reading speed, and download MP3 files.
- **Local Developers / Audio Hobbyists:** Self-host a clean local TTS studio with history tracking, persistent audio file storage, and offline voice catalog filtering.

### 1.2 Core Capabilities
1. High-capacity Text Editor with real-time character count and validation (up to 3,000 chars).
2. Voice Catalog & Library with search (`display_name`, `voice_type`), language filter (`lang`), favorites, and cached sample previews.
3. Asynchronous Job Processing with live polling, progress UI, error diagnostics, and audio player controls.
4. Persistent Audio Storage in local filesystem SQLite DB (`data/app.db` & `data/audio/*.mp3`).
5. Downloadable MP3 audio with custom friendly filenames (`capvoice-{voice-slug}-{timestamp}.mp3`).
6. Full Job History with play, download, settings recall, retry, and delete capabilities.

### 1.3 Scope & Explicit Non-Goals
- **In-Scope (MVP):** Text-to-Speech editor, Voice catalog navigation & preview, TTS job queuing & polling, Local audio persistence & streaming, Job history, Application settings.
- **Explicit Non-Goals (Out of Scope):** User authentication / OAuth, CapCut account login / bypass premium, Subtitles / Speech-to-Text (STT), Voice cloning, Multi-tenant billing / cloud sync, Direct browser requests to CapCut internal endpoints.

---

## 2. Architecture & UX Trade-off Analysis

### 2.1 Evaluated Approaches

| Axis | Option A: Next.js API Subprocess Wrapper | Option B: Decoupled FastAPI + Next.js Monorepo (Recommended) | Option C: Event-Driven Queue (Redis + Celery) |
|---|---|---|---|
| **Architecture** | Next.js API routes spawning `python3 client.py` via `child_process`. | Next.js frontend communicating with a dedicated Python FastAPI service wrapping `CapCutClient` with SQLite + `asyncio.to_thread`. | FastAPI API gateway pushing tasks to Redis; Celery worker nodes executing SDK calls. |
| **SDK Integration** | Fragile CLI string parsing; no long-lived connection or memory reuse. | Robust Python native import (`capcut_tts_api`), adapter interface, blocking SDK calls run in worker thread pool (`to_thread`). | Highly scalable async worker pool. |
| **Complexity** | Low architecture complexity, high runtime brittleness. | Balanced, single-command local run, complete separation of concerns. | High infrastructure overhead (requires Redis server, worker daemon). |
| **Resilience** | Poor error handling during SDK structural updates. | High; isolated raw response parser with fallback heuristics and unit test fixtures. | High runtime isolation, but complex setup for end users. |

### 2.2 Recommendation Decision
**Option B** is selected. It meets all MVP persistence, security, and developer ergonomics goals without adding unnecessary infrastructure dependencies like Redis.

---

## 3. Frontend Design System & Aesthetics (per `frontend-design` guidance)

### 3.1 Visual Identity: Modern Audio Workstation
- **Theme Concept:** "Precision Dark Studio" — Inspired by professional Digital Audio Workstations (DAWs) and modern AI creative tools. Clean slate backgrounds, soft border highlights, glowing status indicators, and distinct violet/indigo accent lines.
- **Signature Element:** Interactive Waveform Result Card with real-time status pulses (`queued` amber pulse, `processing` active shimmer bar, `completed` audio wave visualization with playback scrubbers).

### 3.2 Token System (OKLCH CSS Variables)

```css
:root {
  --radius: 0.75rem;
  --background: oklch(0.985 0 0);
  --foreground: oklch(0.19 0.015 270);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.19 0.015 270);
  --primary: oklch(0.57 0.23 285);
  --primary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.955 0.006 270);
  --muted-foreground: oklch(0.52 0.02 270);
  --border: oklch(0.90 0.008 270);
  --accent: oklch(0.96 0.015 285);
  --accent-foreground: oklch(0.35 0.15 285);
}

.dark {
  --background: oklch(0.145 0.012 270);
  --foreground: oklch(0.96 0.005 270);
  --card: oklch(0.18 0.015 270);
  --card-foreground: oklch(0.96 0.005 270);
  --primary: oklch(0.70 0.20 285);
  --primary-foreground: oklch(0.14 0.01 270);
  --muted: oklch(0.23 0.015 270);
  --muted-foreground: oklch(0.70 0.015 270);
  --border: oklch(0.28 0.015 270);
  --accent: oklch(0.25 0.05 285);
  --accent-foreground: oklch(0.90 0.10 285);
}
```

### 3.3 Typography & Scale
- **UI & Display Font:** `Geist` (Inter fallback).
- **Code & Tech Specs:** `Geist Mono`.
- **Type Scale:** Title 28px/Semibold, Section 18px/Medium, Body 14px/Regular, Caption/Meta 12px/Regular.

---

## 4. Information Architecture & Layout

### 4.1 Sitemap & Structure
- `/` — **Text to Speech Studio** (Composer + Voice Panel + Result Card)
- `/voices` — **Voice Library Catalog** (Search, Filter, Samples, Favorites)
- `/history` — **Generation History** (Table / Card List, Re-play, Download, Delete)
- `/settings` — **Preferences & System Health** (Theme, Defaults, Health Status)

### 4.2 Desktop Studio Layout Architecture (>= 1280px)
- Fixed left sidebar navigation (240px).
- Main content container (Max 1440px):
  - Left Pane (2fr): Text Composer & Job Status / Audio Result Card.
  - Right Pane (1fr): Voice Selector Panel, Speed Controls, Format Settings, Generate Action Button.

### 4.3 Mobile Layout Architecture (< 768px)
- Collapsible Navigation Sheet triggered via Header Hamburger.
- Text Composer and Voice Settings stacked vertically.
- Bottom Sticky Action Dock containing the Voice summary pill and "Generate Audio" button.

---

## 5. System Architecture & Backend Modules

### 5.1 System Flow Diagram

```text
Browser (Next.js Client)
  ├─> POST /api/v1/tts/jobs ─────────> FastAPI Server
  │                                       │ (Validate & store queued job in SQLite DB)
  │                                       ├─> Background Worker Task
  │                                       │    ├─> asyncio.to_thread(CapCutProvider.synthesize)
  │                                       │    │    └─> CapCutClient.generate_speech()
  │                                       │    │         └─> CapCut Internal Endpoints
  │                                       │    ├─> Raw Response Parser (extract_audio_urls)
  │                                       │    └─> httpx Audio Stream Downloader
  │                                       │         └─> Save file to data/audio/{job_id}.mp3
  │                                       │         └─> Update DB status = 'completed'
  ├─> GET /api/v1/tts/jobs/{id} <─────────┤
  └─> GET /api/v1/tts/jobs/{id}/audio <───┘ (Streams local MP3 binary)
```

### 5.2 Provider Adapter Boundary (`apps/api/app/providers/capcut_provider.py`)
- Wraps `capcut_tts_api.CapCutClient`.
- Implements `TTSProvider` protocol.
- Executes `client.generate_speech` in blocking thread pool.
- Isolates upstream variations from application logic.

### 5.3 Raw Response Parser (`apps/api/app/services/provider_response_parser.py`)
- Recursive JSON walker scanning payload for audio URL fields (`audio_url`, `play_url`, `download_url`, `uri`).
- Validates HTTP/HTTPS scheme and filters out non-audio endpoints.
- Verifies MIME content types (`audio/mpeg`, `audio/mp3`, `application/octet-stream`).

### 5.4 Data Storage & Database Model (`apps/api/app/models/tts_job.py`)

Table `tts_jobs`:
- `id` (UUID string, PK)
- `kind` (string: "generation" | "preview")
- `text` (text)
- `text_hash` (string, indexed)
- `voice_type` (string, indexed)
- `voice_display_name` (string)
- `resource_id` (string, nullable)
- `language_code` (string)
- `rate` (float)
- `status` (string, indexed: "queued" | "processing" | "completed" | "failed" | "cancelled")
- `progress` (integer, nullable)
- `provider_task_id` (string, nullable)
- `provider_token` (string, nullable - redacted in API outputs)
- `audio_path` (string, nullable)
- `audio_mime_type` (string, nullable)
- `audio_file_size` (integer, nullable)
- `raw_response_path` (string, nullable)
- `error_code` (string, nullable)
- `error_message` (text, nullable)
- `attempt_count` (integer, default 0)
- `created_at` (datetime, indexed)
- `updated_at` (datetime)
- `completed_at` (datetime, nullable)

---

## 6. API Contracts & Validation

### 6.1 Endpoints Summary
- `GET /api/v1/health` — System status, catalog metadata, provider configuration status.
- `GET /api/v1/voices` — Filtered catalog items list (`language`, `q`, `page`, `page_size`).
- `GET /api/v1/voices/{voice_type}` — Detailed voice item.
- `POST /api/v1/voices/{voice_type}/preview` — Generates/returns cached voice preview sample.
- `POST /api/v1/tts/jobs` — Enqueues new TTS generation job (`202 Accepted`).
- `GET /api/v1/tts/jobs/{job_id}` — Gets job status and metadata.
- `GET /api/v1/tts/jobs` — Lists job history (paginated, filterable by status).
- `GET /api/v1/tts/jobs/{job_id}/audio` — Streams stored MP3 audio file.
- `GET /api/v1/tts/jobs/{job_id}/download` — Forces attachment MP3 download with friendly filename.
- `POST /api/v1/tts/jobs/{job_id}/retry` — Re-enqueues a new job with identical settings.
- `DELETE /api/v1/tts/jobs/{job_id}` — Removes database job record and deletes local files.

### 6.2 Error Responses & Error Codes
Standard error envelope:
```json
{
  "error": {
    "code": "VOICE_NOT_FOUND",
    "message": "The selected voice is no longer available in the catalog.",
    "requestId": "req_123456"
  }
}
```
Error Codes: `VALIDATION_ERROR`, `VOICE_NOT_FOUND`, `CATALOG_UNAVAILABLE`, `PROVIDER_UNAVAILABLE`, `PROVIDER_REJECTED`, `PROVIDER_TIMEOUT`, `AUDIO_URL_NOT_FOUND`, `AUDIO_DOWNLOAD_FAILED`, `AUDIO_INVALID_CONTENT`, `JOB_NOT_FOUND`, `JOB_NOT_READY`, `INTERNAL_ERROR`.

---

## 7. Testing, Security & Quality Assurance

1. **Unit Tests (FastAPI / pytest):** Catalog loading, job state transitions, provider error mapping, raw response JSON parser recursively extracting nested audio URLs, audio downloader file size limit enforcements.
2. **Frontend Tests (Vitest + React Testing Library):** Text Composer length validation, Character counter warning state, Voice picker filtering & selection, Job status card state rendering.
3. **Mocked E2E Tests (Playwright):** Complete flow from text input, voice selection, simulated job processing, audio player rendering, history updates.
4. **Manual Provider Smoke Test Script (`scripts/smoke_test.py`):** Command line tool to verify direct SDK execution against live provider, inspect raw dict responses, and download output audio.
5. **Security Safeguards:** Redact provider tokens/signed URLs from logs, sanitize request inputs, set 50MB audio download file cap, restrict CORS to configured origins.

---

## 8. Disclaimer Notice
Footer & About modal must explicitly state:
*"CapVoice Studio is an independent open-source project and is not affiliated with or endorsed by CapCut or ByteDance."*
