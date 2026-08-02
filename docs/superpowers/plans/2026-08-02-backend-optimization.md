# Void Melody Backend Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a bounded, restart-safe, observable, and locally authenticated TTS backend without replacing the existing stack.

**Architecture:** SQLite remains durable state and the in-process queue becomes a dispatcher over atomically claimed jobs. Independent workers use reusable CapCut clients and bounded chunk execution; typed failures drive delayed retry, cleanup, and circuit-breaker behavior.

**Tech Stack:** Python 3.9+, FastAPI, SQLAlchemy AsyncSession, SQLite/aiosqlite, Alembic, httpx, CapCut TTS API, FFmpeg, Next.js, Tauri.

## Global Constraints

- Keep FastAPI, SQLite, SQLAlchemy AsyncSession, CapCut TTS, and FFmpeg.
- Default queue concurrency is 2 and chunk concurrency is 1.
- Automatic retry count is 2 after the initial attempt.
- Real CapCut calls are excluded from automated tests.
- Preserve existing request/response compatibility except retry returning a new ID.

---

### Task 1: Correctness and bounded concurrency

- [x] Add failing tests for bounded scheduling, session isolation, chunk limits, and progress throttling.
- [x] Add settings, immutable job/result types, bounded executor, and progress reporter.
- [x] Refactor the worker so only the parent coroutine writes ORM state.
- [x] Run targeted and full backend tests; commit on `codex/backend-opt-p1-concurrency`.

### Task 2: Typed errors, rate, and retry

- [x] Add failing tests for retry classification, retry count/backoff, and FFmpeg non-regeneration.
- [x] Add `TTSJobError`, provider/download error mapping, delayed retry, and one-place rate application.
- [x] Run targeted and full backend tests; commit on `codex/backend-opt-p2-retry`.

### Task 3: Persistent queue behavior

- [x] Add failing tests for atomic claim, dedupe, restart recovery, and graceful shutdown.
- [x] Implement queue membership locking, per-worker providers, recovery, and shutdown requeue.
- [x] Run targeted and full backend tests; commit on `codex/backend-opt-p3-queue`.

### Task 4: SQLite and Alembic

- [x] Add migration tests for fresh, legacy, current unversioned, and invalid schemas.
- [x] Enable SQLite pragmas, runtime Alembic configuration, backups, and guarded legacy adoption.
- [x] Run migration and concurrency tests; commit on `codex/backend-opt-p4-sqlite`.

### Task 5: Provider and network reuse

- [x] Add failing tests for catalog invalidation, client reuse, response ranking, and breaker transitions.
- [x] Implement voice catalog caching, persistent clients, validation, and a shared circuit breaker.
- [x] Run targeted and full backend tests; commit on `codex/backend-opt-p5-provider`.

### Task 6: Audio lifecycle and immutable retry

- [x] Add failing tests for cleanup, final validation, conversion races, and new-ID retry.
- [x] Implement guaranteed cleanup, atomic output, locked M4A conversion, and retry cloning.
- [x] Run targeted and full backend tests; commit on `codex/backend-opt-p6-audio`.

### Task 7: Health, logs, and local auth

- [x] Add failing tests for health status, auth matrix, log redaction, and authenticated media helpers.
- [x] Add live/ready endpoints, JSON logging, production token middleware, and desktop token propagation.
- [x] Run API/web tests and builds; commit on `codex/backend-opt-p7-observability-security`.

### Task 8: Integration gate

- [x] Run the complete automated test suites and migration matrix.
- [x] Build the web app, PyInstaller sidecar, and unsigned desktop bundle; run Cargo checks.
- [x] Run a random-port, token-authenticated localhost smoke test without CapCut.
- [x] Audit the acceptance checklist on `codex/backend-opt-integration`.
