# vieneu-core

Framework-agnostic contracts, capabilities, errors, and fixtures for the
VieNeu-TTS integration in VoidMelody.

## Non-goals (this package must NOT depend on)

- FastAPI, Starlette
- SQLAlchemy, Alembic
- Next.js, React, Tauri
- VoidMelody queue, database models, or global application state

It depends only on the Python standard library at the contract level. The
real VieNeu engine (`vieneu`) is only needed by the engine implementation
(phases 4–5), not by the contracts here.

## What's here

- `src/vieneu_core/contracts.py` — `Voice`, `Style`, `SynthesizeRequest`,
  `SynthesizeResult`, `AudioFormat`, and the `VieneuEngine` Protocol.
- `src/vieneu_core/capabilities.py` — `Capabilities`, `ProviderDescriptor`,
  `default_capabilities()`.
- `src/vieneu_core/errors.py` — `VieneuCoreError` hierarchy + error code
  constants.
- `src/vieneu_core/fixtures.py` — deterministic in-memory fixtures for tests.
- `index.ts` — TypeScript types mirroring the Python contracts for the
  VoidMelody web frontend (type-only; imported in phases 5+).

## Tests

```bash
cd packages/vieneu-core
uv sync --group dev
uv run pytest
```