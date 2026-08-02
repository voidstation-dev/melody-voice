# Void Melody Backend Optimization Design

## Goal

Make the existing FastAPI, SQLite, SQLAlchemy, CapCut TTS, and FFmpeg backend safe under concurrent jobs, recoverable across restarts, bounded in memory and provider load, and secure for local desktop use.

## Architecture

The queue remains in-process while SQLite remains the durable source of job state. Queue workers atomically claim queued rows, own independent database sessions and provider instances, and run a bounded chunk executor. Chunk calls operate on immutable job snapshots and return `ChunkResult` values; only the parent job coroutine updates ORM state and throttles progress commits.

Provider, download, concat, and validation are separate stages. Typed errors decide whether a failure may be retried. Automatic retries are limited to two after the initial attempt and are delayed without occupying a worker. Temporary audio artifacts are removed on failure, cancellation, restart, and shutdown.

SQLite runs in WAL mode. Alembic becomes the schema source of truth, with a guarded adoption path for databases created by the previous `create_all()` startup. The adoption path backs up the file, validates the known legacy schema, adds missing batch columns, and stamps the baseline before upgrading.

Each queue worker owns a reusable CapCut client, while the queue shares a circuit breaker. The voice catalog is cached by modification time. Audio URLs are ranked by known response paths and downloaded content is validated before use.

Production desktop startup binds to localhost, chooses a random port, and requires a per-launch `X-Melody-Token`. Liveness is public for bootstrapping; readiness and business endpoints are authenticated. Browser media is fetched as authenticated blobs because native audio and anchor elements cannot attach the header.

## Compatibility

- Existing TTS job request and response shapes remain valid.
- `POST /tts/jobs/{id}/retry` returns a new job and leaves the original immutable.
- `/api/v1/health` remains as a liveness compatibility alias; `/health/live` and `/health/ready` are added.
- Development and tests may run without a token; production fails startup without one.
- Real CapCut requests never run in automated tests.

## Verification

Each phase has targeted tests and a full backend regression gate. The final gate covers API and web tests, migration fixtures, web and sidecar builds, Cargo checks, authenticated localhost smoke tests, graceful shutdown, and artifact cleanup.
