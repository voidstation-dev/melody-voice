# CapVoice Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build CapVoice Studio, a full-stack, local-first Text-to-Speech studio web app using Next.js App Router, shadcn/ui, Tailwind CSS, FastAPI, SQLite, and capcut-tts-api.

**Architecture:** Monorepo with `apps/web` (Next.js frontend) and `apps/api` (FastAPI backend). Backend wraps `capcut_tts_api.CapCutClient` in an isolated provider adapter, processes background jobs, downloads MP3s to local storage, and serves them via streaming endpoints.

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form, Zod, Python 3.11, FastAPI, SQLAlchemy 2, aiosqlite, httpx, capcut-tts-api.

## Global Constraints

- **Language & Runtime:** Python >= 3.9 (3.11 recommended), Node.js >= 18, pnpm >= 8.
- **Frontend Stack:** Next.js App Router, TypeScript strict mode, Tailwind CSS, shadcn/ui, Lucide React, TanStack Query v5.
- **Backend Stack:** FastAPI, Pydantic v2, SQLAlchemy 2, aiosqlite, httpx, tenacity.
- **Vendor SDK:** Pin commit from `https://github.com/K07VN/capcut-tts-api.git` under `vendor/capcut-tts-api`.
- **Database & Storage:** Local SQLite database at `data/app.db`, MP3 files stored at `data/audio/{job_id}.mp3`.
- **Security & Privacy:** Do not call CapCut API endpoints directly from the browser. Do not expose provider raw tokens or signed URLs to client UI. Do not log user text content or secrets.

---

### Task 1: Monorepo Setup & Workspace Infrastructure

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `docker-compose.yml`

**Interfaces:**
- Consumes: System package managers (`pnpm`, `python`, `git`).
- Produces: Monorepo workspace configuration, data directories, environment template.

- [ ] **Step 1: Create root pnpm workspace files**

Create `pnpm-workspace.yaml`:
```yaml
packages:
  - "apps/*"
```

Create `package.json`:
```json
{
  "name": "capvoice-studio-monorepo",
  "private": true,
  "scripts": {
    "dev:web": "pnpm --dir apps/web dev",
    "dev:api": "uvicorn app.main:app --app-dir apps/api --reload --port 8000",
    "lint:web": "pnpm --dir apps/web lint",
    "test:web": "pnpm --dir apps/web test",
    "test:api": "pytest apps/api/tests -v"
  }
}
```

- [ ] **Step 2: Create directory structure and environment files**

Create `.env.example`:
```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
DATABASE_URL=sqlite+aiosqlite:///../../data/app.db
AUDIO_STORAGE_DIR=../../data/audio
PREVIEW_STORAGE_DIR=../../data/previews
RAW_RESPONSE_DIR=../../data/raw-responses
CAPCUT_CATALOG_PATH=../../vendor/capcut-tts-api/Voice.json
TTS_MAX_TEXT_CHARS=3000
TTS_MIN_RATE=0.5
TTS_MAX_RATE=2.0
TTS_PROVIDER_TIMEOUT_SECONDS=90
TTS_AUDIO_MAX_BYTES=52428800
SAVE_RAW_PROVIDER_RESPONSES=true
LOG_LEVEL=INFO
```

Create `.gitignore`:
```gitignore
node_modules
.venv
__pycache__
*.pyc
.next
dist
data/app.db
data/audio/*
data/previews/*
data/raw-responses/*
!data/audio/.gitkeep
!data/previews/.gitkeep
!data/raw-responses/.gitkeep
.env
```

Create `docker-compose.yml`:
```yaml
services:
  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./vendor/capcut-tts-api/Voice.json:/app/vendor/capcut-tts-api/Voice.json:ro

  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - api
```

- [ ] **Step 3: Verify setup and commit**

Run: `mkdir -p data/audio data/previews data/raw-responses apps vendor`
Expected: Folders created successfully.

Run: `git status`
Expected: Clean untracked files listed.

```bash
git add package.json pnpm-workspace.yaml .env.example .gitignore docker-compose.yml
git commit -m "chore: setup monorepo workspace and data directories"
```

---

### Task 2: Backend Core Configuration & Database Setup

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/config.py`
- Create: `apps/api/app/database.py`
- Create: `apps/api/app/models/tts_job.py`
- Test: `apps/api/tests/test_database.py`

**Interfaces:**
- Consumes: Environment variables from `.env`.
- Produces: `Settings` object, SQLAlchemy async engine, `Base` model, `TTSJobModel`.

- [ ] **Step 1: Write failing database test**

Create `apps/api/tests/test_database.py`:
```python
import pytest
from sqlalchemy import select
from app.database import get_async_session, init_database
from app.models.tts_job import TTSJobModel

@pytest.mark.asyncio
async def test_init_db_creates_tables():
    await init_database()
    async for session in get_async_session():
        result = await session.execute(select(TTSJobModel))
        assert result.scalars().all() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest apps/api/tests/test_database.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app'".

- [ ] **Step 3: Implement pyproject.toml, config.py, database.py, and models/tts_job.py**

Create `apps/api/pyproject.toml`:
```toml
[project]
name = "capvoice-api"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.28.0",
    "pydantic-settings>=2.2.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.20.0",
    "httpx>=0.27.0",
    "python-multipart>=0.0.9",
    "tenacity>=8.2.0"
]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
```

Create `apps/api/app/config.py`:
```python
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "sqlite+aiosqlite:///../../data/app.db"
    audio_storage_dir: Path = Path("../../data/audio")
    preview_storage_dir: Path = Path("../../data/previews")
    raw_response_dir: Path = Path("../../data/raw-responses")
    capcut_catalog_path: Path = Path("../../vendor/capcut-tts-api/Voice.json")
    tts_max_text_chars: int = 3000
    tts_min_rate: float = 0.5
    tts_max_rate: float = 2.0
    tts_provider_timeout_seconds: float = 90.0
    tts_audio_max_bytes: int = 52428800
    save_raw_provider_responses: bool = True
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

Create `apps/api/app/database.py`:
```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

Create `apps/api/app/models/tts_job.py`:
```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class TTSJobModel(Base):
    __tablename__ = "tts_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kind: Mapped[str] = mapped_column(String(20), default="generation", index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    voice_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    voice_display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language_code: Mapped[str] = mapped_column(String(20), nullable=False)
    rate: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), index=True, default="queued")
    progress: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    audio_file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_response_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_database.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/pyproject.toml apps/api/app/config.py apps/api/app/database.py apps/api/app/models/tts_job.py apps/api/tests/test_database.py
git commit -m "feat(backend): setup config, database engine and tts_job model"
```

---

### Task 3: Provider Adapter & Catalog Provider

**Files:**
- Create: `apps/api/app/providers/base.py`
- Create: `apps/api/app/providers/capcut_provider.py`
- Test: `apps/api/tests/test_capcut_provider.py`

**Interfaces:**
- Consumes: Vendor SDK `capcut_tts_api.CapCutClient` and `Voice.json`.
- Produces: `TTSProvider` protocol, `CapCutProvider` class, `ProviderVoice`, `ProviderResult`.

- [ ] **Step 1: Write failing provider adapter unit test**

Create `apps/api/tests/test_capcut_provider.py`:
```python
from pathlib import Path
import pytest
from app.providers.capcut_provider import CapCutProvider

def test_list_voices_from_dummy_catalog(tmp_path: Path):
    catalog_file = tmp_path / "Voice.json"
    catalog_file.write_text('[{"lan": "vi", "lang": "vi-VN", "voice_type": "BV421_vivn_streaming", "display_name": "Nhỏ Ngọt Ngào", "resource_id": "7252594014782755330"}]')

    provider = CapCutProvider(catalog_path=catalog_file)
    voices = provider.list_voices()
    
    assert len(voices) == 1
    assert voices[0].display_name == "Nhỏ Ngọt Ngào"
    assert voices[0].voice_type == "BV421_vivn_streaming"
    assert voices[0].language_code == "vi-VN"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_capcut_provider.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.providers.capcut_provider'".

- [ ] **Step 3: Implement base.py and capcut_provider.py**

Create `apps/api/app/providers/base.py`:
```python
from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class ProviderVoice:
    language_short: str
    language_code: str
    voice_type: str
    display_name: str
    resource_id: str
    captured_at: str | None = None

@dataclass(frozen=True)
class ProviderResult:
    raw_response: dict[str, Any]
    audio_urls: list[str]

class TTSProvider(Protocol):
    def list_voices(self, language: str | None = None) -> list[ProviderVoice]: ...
    def synthesize(
        self,
        *,
        text: str,
        voice_type: str,
        resource_id: str | None,
        rate: float,
    ) -> ProviderResult: ...
```

Create `apps/api/app/providers/capcut_provider.py`:
```python
import json
from pathlib import Path
from typing import Any
from app.providers.base import ProviderResult, ProviderVoice

class CapCutProvider:
    def __init__(self, *, catalog_path: Path, device_path: Path | None = None):
        self.catalog_path = catalog_path
        self.device_path = device_path

    def list_voices(self, language: str | None = None) -> list[ProviderVoice]:
        if not self.catalog_path.exists():
            return []
        
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        voices: list[ProviderVoice] = []
        for item in data:
            lang_code = item.get("lang", "")
            if language and lang_code.lower() != language.lower():
                continue
            voices.append(
                ProviderVoice(
                    language_short=item.get("lan", ""),
                    language_code=lang_code,
                    voice_type=item.get("voice_type", ""),
                    display_name=item.get("display_name", ""),
                    resource_id=item.get("resource_id", ""),
                    captured_at=item.get("captured_at"),
                )
            )
        return voices

    def synthesize(
        self,
        *,
        text: str,
        voice_type: str,
        resource_id: str | None,
        rate: float,
    ) -> ProviderResult:
        from capcut_tts_api import CapCutClient
        from app.services.provider_response_parser import extract_audio_urls

        client = CapCutClient(device=self.device_path) if self.device_path else CapCutClient()
        response: dict[str, Any] = client.generate_speech(
            texts=text,
            voice=voice_type,
            resource_id=resource_id,
            rate=f"{rate:.2f}",
            wait=True,
            poll_interval=1.0,
            timeout=90.0,
        )

        return ProviderResult(
            raw_response=response,
            audio_urls=extract_audio_urls(response),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_capcut_provider.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/providers/base.py apps/api/app/providers/capcut_provider.py apps/api/tests/test_capcut_provider.py
git commit -m "feat(backend): implement provider adapter and catalog parser"
```

---

### Task 4: Recursive Response Parser & Audio Storage Service

**Files:**
- Create: `apps/api/app/services/provider_response_parser.py`
- Create: `apps/api/app/services/audio_storage.py`
- Test: `apps/api/tests/test_response_parser.py`
- Test: `apps/api/tests/test_audio_storage.py`

**Interfaces:**
- Consumes: Raw SDK output dictionaries, HTTP audio stream URLs.
- Produces: `extract_audio_urls(payload)`, `download_audio(url, destination, max_bytes)`.

- [ ] **Step 1: Write failing parser and audio storage tests**

Create `apps/api/tests/test_response_parser.py`:
```python
from app.services.provider_response_parser import extract_audio_urls

def test_extract_audio_urls_nested_json():
    payload = {
        "status": "success",
        "data": {
            "main_audio": '{"play_url": "https://v16-tts.capcut.com/audio/sample.mp3"}',
            "other": "https://example.com/not-audio"
        }
    }
    urls = extract_audio_urls(payload)
    assert len(urls) == 1
    assert urls[0] == "https://v16-tts.capcut.com/audio/sample.mp3"
```

Create `apps/api/tests/test_audio_storage.py`:
```python
from pathlib import Path
import pytest
import respx
from httpx import Response
from app.services.audio_storage import download_audio

@pytest.mark.asyncio
@respx.mock
async def test_download_audio_success(tmp_path: Path):
    target_url = "https://cdn.example.com/audio.mp3"
    respx.get(target_url).mock(return_value=Response(200, content=b"ID3mockaudiodata", headers={"Content-Type": "audio/mpeg"}))

    dest = tmp_path / "test.mp3"
    mime, size = await download_audio(url=target_url, destination=dest)

    assert dest.exists()
    assert mime == "audio/mpeg"
    assert size == 16
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_response_parser.py apps/api/tests/test_audio_storage.py -v`
Expected: FAIL with missing module error.

- [ ] **Step 3: Implement provider_response_parser.py and audio_storage.py**

Create `apps/api/app/services/provider_response_parser.py`:
```python
import json
from typing import Any
from urllib.parse import urlparse

PREFERRED_AUDIO_KEYS = {
    "audio_url", "audioUrl", "download_url", "downloadUrl",
    "play_url", "playUrl", "url", "uri",
}

def _maybe_decode_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value

def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

def extract_audio_urls(payload: Any) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()

    def walk(node: Any, parent_key: str | None = None) -> None:
        node = _maybe_decode_json(node)
        if isinstance(node, dict):
            for key, value in node.items():
                decoded = _maybe_decode_json(value)
                if key in PREFERRED_AUDIO_KEYS and isinstance(decoded, str) and _is_http_url(decoded):
                    if decoded not in seen:
                        seen.add(decoded)
                        results.append(decoded)
                walk(decoded, key)
        elif isinstance(node, list):
            for item in node:
                walk(item, parent_key)
        elif isinstance(node, str) and parent_key in PREFERRED_AUDIO_KEYS and _is_http_url(node):
            if node not in seen:
                seen.add(node)
                results.append(node)

    walk(payload)
    return results
```

Create `apps/api/app/services/audio_storage.py`:
```python
from pathlib import Path
import httpx

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/x-mpeg", "application/octet-stream",
}

async def download_audio(
    *,
    url: str,
    destination: Path,
    max_bytes: int = 50 * 1024 * 1024,
) -> tuple[str, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(".tmp")
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=5) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").split(";")[0].lower()
            if content_type and content_type not in ALLOWED_CONTENT_TYPES:
                raise ValueError(f"Unexpected content type: {content_type}")

            total = 0
            with temp_path.open("wb") as output:
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        if temp_path.exists():
                            temp_path.unlink()
                        raise ValueError("Audio file exceeds maximum size limit")
                    output.write(chunk)

    temp_path.replace(destination)
    return content_type or "audio/mpeg", total
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_response_parser.py apps/api/tests/test_audio_storage.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/provider_response_parser.py apps/api/app/services/audio_storage.py apps/api/tests/test_response_parser.py apps/api/tests/test_audio_storage.py
git commit -m "feat(backend): implement response parser and audio download storage service"
```

---

### Task 5: Background Task Worker & Job Management Service

**Files:**
- Create: `apps/api/app/services/tts_service.py`
- Create: `apps/api/app/workers/tts_worker.py`
- Test: `apps/api/tests/test_tts_worker.py`

**Interfaces:**
- Consumes: `TTSJobModel`, `CapCutProvider`, `download_audio`.
- Produces: `process_tts_job(job_id)`, `create_job()`, `get_job()`, `list_jobs()`.

- [ ] **Step 1: Write failing worker unit test**

Create `apps/api/tests/test_tts_worker.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tts_job import TTSJobModel
from app.workers.tts_worker import execute_tts_job_step

@pytest.mark.asyncio
async def test_worker_updates_job_status_failed_on_error(async_session: AsyncSession):
    job = TTSJobModel(
        text="Xin chào",
        text_hash="hash123",
        voice_type="invalid_voice",
        voice_display_name="Unknown",
        language_code="vi-VN",
        rate=1.0,
        status="queued"
    )
    async_session.add(job)
    await async_session.commit()

    with patch("app.providers.capcut_provider.CapCutProvider.synthesize", side_effect=Exception("Provider error")):
        await execute_tts_job_step(job.id, async_session)

    await async_session.refresh(job)
    assert job.status == "failed"
    assert job.error_code == "PROVIDER_UNAVAILABLE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_tts_worker.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement tts_service.py and tts_worker.py**

Create `apps/api/app/services/tts_service.py`:
```python
import hashlib
from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tts_job import TTSJobModel

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

async def create_tts_job(
    session: AsyncSession,
    *,
    text: str,
    voice_type: str,
    voice_display_name: str,
    language_code: str,
    resource_id: str | None = None,
    rate: float = 1.0,
    kind: str = "generation",
) -> TTSJobModel:
    cleaned_text = text.strip()
    job = TTSJobModel(
        kind=kind,
        text=cleaned_text,
        text_hash=compute_text_hash(cleaned_text),
        voice_type=voice_type,
        voice_display_name=voice_display_name,
        resource_id=resource_id,
        language_code=language_code,
        rate=rate,
        status="queued",
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job

async def get_job_by_id(session: AsyncSession, job_id: str) -> TTSJobModel | None:
    return await session.get(TTSJobModel, job_id)

async def list_jobs(
    session: AsyncSession,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[TTSJobModel], int]:
    stmt = select(TTSJobModel).order_by(TTSJobModel.created_at.desc())
    if status:
        stmt = stmt.where(TTSJobModel.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    jobs = (await session.execute(stmt)).scalars().all()

    return jobs, total
```

Create `apps/api/app/workers/tts_worker.py`:
```python
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.services.audio_storage import download_audio

async def execute_tts_job_step(job_id: str, session: AsyncSession) -> None:
    job = await session.get(TTSJobModel, job_id)
    if not job or job.status != "queued":
        return

    job.status = "processing"
    job.started_at = datetime.now(timezone.utc)
    await session.commit()

    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    
    try:
        result = await asyncio.to_thread(
            provider.synthesize,
            text=job.text,
            voice_type=job.voice_type,
            resource_id=job.resource_id,
            rate=job.rate,
        )

        if settings.save_raw_provider_responses:
            settings.raw_response_dir.mkdir(parents=True, exist_ok=True)
            raw_file = settings.raw_response_dir / f"{job_id}.json"
            raw_file.write_text(json.dumps(result.raw_response, indent=2))
            job.raw_response_path = str(raw_file)

        if not result.audio_urls:
            raise ValueError("AUDIO_URL_NOT_FOUND: No playable audio URL extracted from provider")

        dest = settings.audio_storage_dir / f"{job_id}.mp3"
        mime, size = await download_audio(url=result.audio_urls[0], destination=dest)

        job.status = "completed"
        job.audio_path = str(dest)
        job.audio_mime_type = mime
        job.audio_file_size = size
        job.completed_at = datetime.now(timezone.utc)

    except Exception as exc:
        job.status = "failed"
        job.error_code = "PROVIDER_UNAVAILABLE" if "Provider" in str(exc) else "INTERNAL_ERROR"
        job.error_message = str(exc)
    
    await session.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_tts_worker.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/tts_service.py apps/api/app/workers/tts_worker.py apps/api/tests/test_tts_worker.py
git commit -m "feat(backend): implement job manager service and async background worker"
```

---

### Task 6: FastAPI API Endpoints & Router Setup

**Files:**
- Create: `apps/api/app/schemas/common.py`
- Create: `apps/api/app/schemas/voice.py`
- Create: `apps/api/app/schemas/tts.py`
- Create: `apps/api/app/api/v1/health.py`
- Create: `apps/api/app/api/v1/voices.py`
- Create: `apps/api/app/api/v1/tts_jobs.py`
- Create: `apps/api/app/api/v1/router.py`
- Create: `apps/api/app/main.py`
- Test: `apps/api/tests/test_endpoints.py`

**Interfaces:**
- Consumes: FastAPI routers, Pydantic schemas, DB sessions.
- Produces: HTTP API Endpoints (`/api/v1/health`, `/api/v1/voices`, `/api/v1/tts/jobs`).

- [ ] **Step 1: Write failing endpoint integration tests**

Create `apps/api/tests/test_endpoints.py`:
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["service"] == "capvoice-api"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_endpoints.py -v`
Expected: FAIL with import error or 404.

- [ ] **Step 3: Implement schemas, routes, and main.py**

Create `apps/api/app/schemas/common.py`:
```python
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    message: str
    requestId: str | None = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

Create `apps/api/app/schemas/voice.py`:
```python
from pydantic import BaseModel

class VoiceResponse(BaseModel):
    id: str
    languageCode: str
    languageShort: str
    voiceType: str
    displayName: str
    resourceId: str
    capturedAt: str | None = None

class VoiceListResponse(BaseModel):
    items: list[VoiceResponse]
    page: int
    pageSize: int
    total: int
```

Create `apps/api/app/schemas/tts.py`:
```python
from pydantic import BaseModel, Field

class CreateTTSJobRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    voiceType: str = Field(min_length=1, max_length=150)
    resourceId: str | None = Field(default=None)
    rate: float = Field(default=1.0, ge=0.5, le=2.0)

class TTSJobResponse(BaseModel):
    id: str
    text: str
    textPreview: str
    voiceType: str
    voiceDisplayName: str
    resourceId: str | None
    rate: float
    status: str
    progress: int | None = None
    audioUrl: str | None = None
    downloadUrl: str | None = None
    fileSize: int | None = None
    errorCode: str | None = None
    errorMessage: str | None = None
    createdAt: str
    updatedAt: str
    completedAt: str | None = None

class TTSJobListResponse(BaseModel):
    items: list[TTSJobResponse]
    page: int
    pageSize: int
    total: int
```

Create `apps/api/app/api/v1/health.py`:
```python
from fastapi import APIRouter
from app.config import settings
from app.providers.capcut_provider import CapCutProvider

router = APIRouter()

@router.get("/health")
async def health_check():
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    voices = provider.list_voices()
    return {
        "status": "ok",
        "service": "capvoice-api",
        "provider": {
            "name": "capcut-tts-api",
            "configured": True,
        },
        "catalog": {
            "voiceCount": len(voices),
            "latestCapturedAt": voices[0].captured_at if voices else None,
        },
    }
```

Create `apps/api/app/api/v1/voices.py`:
```python
from fastapi import APIRouter, HTTPException, Query
from app.config import settings
from app.providers.capcut_provider import CapCutProvider
from app.schemas.voice import VoiceListResponse, VoiceResponse

router = APIRouter()

@router.get("/voices", response_model=VoiceListResponse)
async def list_voices(
    language: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    raw_voices = provider.list_voices(language=language)
    
    if q:
        query_str = q.lower()
        raw_voices = [v for v in raw_voices if query_str in v.display_name.lower() or query_str in v.voice_type.lower()]

    total = len(raw_voices)
    start = (page - 1) * page_size
    items = [
        VoiceResponse(
            id=v.voice_type,
            languageCode=v.language_code,
            languageShort=v.language_short,
            voiceType=v.voice_type,
            displayName=v.display_name,
            resourceId=v.resource_id,
            capturedAt=v.captured_at,
        )
        for v in raw_voices[start : start + page_size]
    ]

    return VoiceListResponse(items=items, page=page, pageSize=page_size, total=total)
```

Create `apps/api/app/api/v1/tts_jobs.py`:
```python
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_async_session
from app.models.tts_job import TTSJobModel
from app.providers.capcut_provider import CapCutProvider
from app.schemas.tts import CreateTTSJobRequest, TTSJobListResponse, TTSJobResponse
from app.services.tts_service import create_tts_job, get_job_by_id, list_jobs
from app.workers.tts_worker import execute_tts_job_step

router = APIRouter()

def serialize_job(job: TTSJobModel) -> TTSJobResponse:
    text_prev = job.text[:80] + "..." if len(job.text) > 80 else job.text
    return TTSJobResponse(
        id=job.id,
        text=job.text,
        textPreview=text_prev,
        voiceType=job.voice_type,
        voiceDisplayName=job.voice_display_name,
        resourceId=job.resource_id,
        rate=job.rate,
        status=job.status,
        progress=job.progress,
        audioUrl=f"/api/v1/tts/jobs/{job.id}/audio" if job.status == "completed" else None,
        downloadUrl=f"/api/v1/tts/jobs/{job.id}/download" if job.status == "completed" else None,
        fileSize=job.audio_file_size,
        errorCode=job.error_code,
        errorMessage=job.error_message,
        createdAt=job.created_at.isoformat(),
        updatedAt=job.updated_at.isoformat(),
        completedAt=job.completed_at.isoformat() if job.completed_at else None,
    )

@router.post("/tts/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=TTSJobResponse)
async def create_job_endpoint(
    req: CreateTTSJobRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    voices = provider.list_voices()
    matched = next((v for v in voices if v.voice_type == req.voiceType), None)
    
    if not matched:
        raise HTTPException(status_code=422, detail="VOICE_NOT_FOUND: Selected voice type does not exist in catalog")

    job = await create_tts_job(
        session,
        text=req.text,
        voice_type=req.voiceType,
        voice_display_name=matched.display_name,
        language_code=matched.language_code,
        resource_id=matched.resource_id,
        rate=req.rate,
    )

    background_tasks.add_task(execute_tts_job_step, job.id, session)
    return serialize_job(job)

@router.get("/tts/jobs/{job_id}", response_model=TTSJobResponse)
async def get_job_endpoint(job_id: str, session: AsyncSession = Depends(get_async_session)):
    job = await get_job_by_id(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
    return serialize_job(job)

@router.get("/tts/jobs/{job_id}/audio")
async def stream_audio_endpoint(job_id: str, session: AsyncSession = Depends(get_async_session)):
    job = await get_job_by_id(session, job_id)
    if not job or job.status != "completed" or not job.audio_path:
        raise HTTPException(status_code=404, detail="AUDIO_NOT_READY")
    return FileResponse(path=job.audio_path, media_type="audio/mpeg", filename=f"capvoice-{job.id}.mp3")
```

Create `apps/api/app/api/v1/router.py`:
```python
from fastapi import APIRouter
from app.api.v1 import health, voices, tts_jobs

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(voices.router, tags=["Voices"])
api_router.include_router(tts_jobs.router, tags=["TTS Jobs"])
```

Create `apps/api/app/main.py`:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.config import settings
from app.database import init_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    yield

app = FastAPI(title="CapVoice Studio API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.include_router(api_router, prefix="/api/v1")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=apps/api pytest apps/api/tests/test_endpoints.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/
git commit -m "feat(backend): add FastAPI routers and HTTP API endpoints"
```

---

### Task 7: Smoke Test Script & Provider Integration Verification

**Files:**
- Create: `scripts/smoke_test.py`
- Test: `scripts/smoke_test.py` (manual execution)

**Interfaces:**
- Consumes: Live `CapCutProvider`.
- Produces: CLI diagnostics output, downloaded sample `.mp3`.

- [ ] **Step 1: Implement scripts/smoke_test.py**

Create `scripts/smoke_test.py`:
```python
import argparse
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from app.config import settings
from app.providers.capcut_provider import CapCutProvider

def main():
    parser = argparse.ArgumentParser(description="CapVoice Studio Live Provider Smoke Test")
    parser.add_argument("--voice", default="BV421_vivn_streaming", help="Voice type identifier")
    parser.add_argument("--text", default="Xin chào, đây là bài kiểm tra giọng đọc.", help="Text content to synthesize")
    args = parser.parse_args()

    print(f"[+] Initializing provider with catalog: {settings.capcut_catalog_path}")
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    
    voices = provider.list_voices()
    print(f"[+] Loaded catalog voices: {len(voices)}")
    
    target_voice = next((v for v in voices if v.voice_type == args.voice), None)
    if not target_voice:
        print(f"[!] Error: Voice '{args.voice}' not found in catalog.")
        sys.exit(1)
        
    print(f"[+] Found voice: {target_voice.display_name} ({target_voice.voice_type})")
    print(f"[+] Requesting synthesis for: '{args.text}'...")

    try:
        res = provider.synthesize(
            text=args.text,
            voice_type=target_voice.voice_type,
            resource_id=target_voice.resource_id,
            rate=1.0,
        )
        print(f"[+] Raw Response Keys: {list(res.raw_response.keys())}")
        print(f"[+] Extracted Audio URLs: {res.audio_urls}")
        if res.audio_urls:
            print(f"[✓] SMOKE TEST SUCCESS: Extracted playable audio URL: {res.audio_urls[0]}")
        else:
            print("[!] Warning: No audio URLs extracted from response.")
    except Exception as e:
        print(f"[!] Provider synthesis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run smoke test script help to verify interface**

Run: `python scripts/smoke_test.py --help`
Expected: Help output listing `--voice` and `--text` flags.

- [ ] **Step 3: Commit**

```bash
git add scripts/smoke_test.py
git commit -m "feat(scripts): add live provider smoke test diagnostic script"
```

---

### Task 8: Frontend Next.js Project & Design Token System Setup

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/src/app/globals.css`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/components/providers/theme-provider.tsx`
- Create: `apps/web/src/components/providers/query-provider.tsx`

**Interfaces:**
- Consumes: Tailwind CSS OKLCH tokens, next-themes, TanStack Query.
- Produces: React root layout with Theme and Query providers.

- [ ] **Step 1: Initialize frontend package.json**

Create `apps/web/package.json`:
```json
{
  "name": "capvoice-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest run"
  },
  "dependencies": {
    "@hookform/resolvers": "^3.3.4",
    "@tanstack/react-query": "^5.28.0",
    "clsx": "^2.1.0",
    "date-fns": "^3.6.0",
    "lucide-react": "^0.359.0",
    "next": "^14.1.4",
    "next-themes": "^0.3.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.51.1",
    "sonner": "^1.4.3",
    "tailwind-merge": "^2.2.2",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20.11.30",
    "@types/react": "^18.2.67",
    "@types/react-dom": "^18.2.22",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.4.3",
    "vitest": "^1.4.0"
  }
}
```

- [ ] **Step 2: Implement globals.css with Studio Theme variables**

Create `apps/web/src/app/globals.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --radius: 0.75rem;
    --background: 0 0% 100%;
    --foreground: 224 71.4% 4.1%;
    --card: 0 0% 100%;
    --card-foreground: 224 71.4% 4.1%;
    --primary: 262.1 83.3% 57.8%;
    --primary-foreground: 210 20% 98%;
    --muted: 220 14.3% 95.9%;
    --muted-foreground: 220 8.9% 46.1%;
    --border: 220 13% 91%;
  }

  .dark {
    --background: 224 71.4% 4.1%;
    --foreground: 210 20% 98%;
    --card: 224 71.4% 6%;
    --card-foreground: 210 20% 98%;
    --primary: 263.4 70% 50.4%;
    --primary-foreground: 210 20% 98%;
    --muted: 215 27.9% 16.9%;
    --muted-foreground: 217.9 10.6% 64.9%;
    --border: 215 27.9% 16.9%;
  }
}

body {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
```

- [ ] **Step 3: Implement ThemeProvider, QueryProvider and Root Layout**

Create `apps/web/src/components/providers/theme-provider.tsx`:
```tsx
"use client"
import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { type ThemeProviderProps } from "next-themes/dist/types"

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
```

Create `apps/web/src/components/providers/query-provider.tsx`:
```tsx
"use client"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: false,
      },
    },
  }))
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
```

Create `apps/web/src/app/layout.tsx`:
```tsx
import "./globals.css"
import { ThemeProvider } from "@/components/providers/theme-provider"
import { QueryProvider } from "@/components/providers/query-provider"

export const metadata = {
  title: "CapVoice Studio",
  description: "Local-first Text to Speech Studio",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryProvider>
          <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
            {children}
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/package.json apps/web/src/app/globals.css apps/web/src/app/layout.tsx apps/web/src/components/providers/
git commit -m "feat(frontend): setup Next.js project layout and theme design tokens"
```

---

### Task 9: Frontend Types, API Client & Data Hooks

**Files:**
- Create: `apps/web/src/types/voice.ts`
- Create: `apps/web/src/types/tts-job.ts`
- Create: `apps/web/src/lib/api-client.ts`
- Create: `apps/web/src/hooks/use-voices.ts`
- Create: `apps/web/src/hooks/use-tts-job.ts`

**Interfaces:**
- Consumes: Backend `/api/v1/*` endpoints.
- Produces: `Voice`, `TTSJob` TypeScript types, `apiFetch`, React Query custom hooks.

- [ ] **Step 1: Create TypeScript type definitions**

Create `apps/web/src/types/voice.ts`:
```ts
export type Voice = {
  id: string
  languageCode: string
  languageShort: string
  voiceType: string
  displayName: string
  resourceId: string
  capturedAt: string | null
}

export type VoiceListResponse = {
  items: Voice[]
  page: number
  pageSize: number
  total: number
}
```

Create `apps/web/src/types/tts-job.ts`:
```ts
export type TTSJobStatus = "queued" | "processing" | "completed" | "failed" | "cancelled"

export type TTSJob = {
  id: string
  text: string
  textPreview: string
  voiceType: string
  voiceDisplayName: string
  resourceId: string | null
  rate: number
  status: TTSJobStatus
  progress: number | null
  audioUrl: string | null
  downloadUrl: string | null
  fileSize: number | null
  errorCode: string | null
  errorMessage: string | null
  createdAt: string
  updatedAt: string
  completedAt: string | null
}
```

- [ ] **Step 2: Create API fetcher & React Query hooks**

Create `apps/web/src/lib/api-client.ts`:
```ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  constructor(message: string, public status: number, public code?: string) {
    super(message)
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(body?.detail ?? "Request failed", response.status, body?.code)
  }
  return response.json() as Promise<T>
}
```

Create `apps/web/src/hooks/use-voices.ts`:
```ts
import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api-client"
import { VoiceListResponse } from "@/types/voice"

export function useVoices(language?: string, q?: string) {
  return useQuery({
    queryKey: ["voices", language, q],
    queryFn: () => {
      const params = new URLSearchParams()
      if (language) params.set("language", language)
      if (q) params.set("q", q)
      return apiFetch<VoiceListResponse>(`/api/v1/voices?${params.toString()}`)
    },
  })
}
```

Create `apps/web/src/hooks/use-tts-job.ts`:
```ts
import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api-client"
import { TTSJob } from "@/types/tts-job"

export function useTTSJob(jobId: string | null) {
  return useQuery({
    queryKey: ["tts-job", jobId],
    queryFn: () => apiFetch<TTSJob>(`/api/v1/tts/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === "queued" || status === "processing" ? 1000 : false
    },
  })
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/types/ apps/web/src/lib/api-client.ts apps/web/src/hooks/
git commit -m "feat(frontend): add TypeScript types, API client and TanStack data hooks"
```

---

### Task 10: App Shell & Responsive Layout Architecture

**Files:**
- Create: `apps/web/src/components/app-shell/app-header.tsx`
- Create: `apps/web/src/components/app-shell/app-sidebar.tsx`
- Create: `apps/web/src/components/app-shell/page-container.tsx`

**Interfaces:**
- Consumes: Header status indicators, navigation tabs (`/`, `/voices`, `/history`, `/settings`).
- Produces: App shell layout wrapper.

- [ ] **Step 1: Implement App Header & Sidebar UI**

Create `apps/web/src/components/app-shell/app-header.tsx`:
```tsx
"use client"
import Link from "next/link"
import { Volume2, Activity } from "lucide-react"

export function AppHeader() {
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
          <Volume2 className="h-5 w-5" />
        </div>
        <span className="text-lg font-bold tracking-tight">CapVoice Studio</span>
      </div>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-emerald-500">
          <Activity className="h-3.5 w-3.5" /> API Ready
        </span>
      </div>
    </header>
  )
}
```

Create `apps/web/src/components/app-shell/app-sidebar.tsx`:
```tsx
"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Mic, Library, History, Settings } from "lucide-react"

const navItems = [
  { label: "Studio", href: "/", icon: Mic },
  { label: "Voice Library", href: "/voices", icon: Library },
  { label: "History", href: "/history", icon: History },
  { label: "Settings", href: "/settings", icon: Settings },
]

export function AppSidebar() {
  const pathname = usePathname()
  return (
    <aside className="hidden md:flex w-60 flex-col border-r border-border bg-card p-4">
      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
```

Create `apps/web/src/components/app-shell/page-container.tsx`:
```tsx
import { AppHeader } from "./app-header"
import { AppSidebar } from "./app-sidebar"

export function PageContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <AppHeader />
      <div className="flex flex-1">
        <AppSidebar />
        <main className="flex-1 p-6 md:p-8">{children}</main>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/app-shell/
git commit -m "feat(frontend): create App Shell header, sidebar and main container layout"
```

---

### Task 11: Text to Speech Studio Components & Synthesis Page

**Files:**
- Create: `apps/web/src/components/tts/text-composer.tsx`
- Create: `apps/web/src/components/tts/voice-settings-panel.tsx`
- Create: `apps/web/src/components/tts/job-status-card.tsx`
- Create: `apps/web/src/components/tts/audio-result-card.tsx`
- Create: `apps/web/src/components/tts/tts-studio.tsx`
- Modify: `apps/web/src/app/page.tsx`

**Interfaces:**
- Consumes: `useVoices`, `useTTSJob`, `apiFetch`.
- Produces: Complete Interactive TTS Studio experience.

- [ ] **Step 1: Implement Text Composer component with character counter**

Create `apps/web/src/components/tts/text-composer.tsx`:
```tsx
"use client"
type TextComposerProps = {
  value: string
  onChange: (val: string) => void
  maxLength: number
  disabled?: boolean
}

export function TextComposer({ value, onChange, maxLength, disabled }: TextComposerProps) {
  const currentLen = value.length
  const warning = currentLen >= maxLength * 0.85

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="font-medium">Script Input</span>
        <span className={warning ? "text-amber-500 font-bold" : ""}>
          {currentLen} / {maxLength} chars
        </span>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        maxLength={maxLength}
        placeholder="Nhập nội dung cần chuyển thành giọng nói tại đây..."
        className="min-h-[280px] w-full resize-y bg-transparent text-sm focus:outline-none disabled:opacity-50"
      />
    </div>
  )
}
```

- [ ] **Step 2: Implement Voice Settings Panel and Studio container**

Create `apps/web/src/components/tts/voice-settings-panel.tsx`:
```tsx
"use client"
import { Voice } from "@/types/voice"

type VoiceSettingsPanelProps = {
  voices: Voice[]
  selectedVoice: string
  onSelectVoice: (v: string) => void
  rate: number
  onRateChange: (r: number) => void
  onGenerate: () => void
  isSubmitting: boolean
}

export function VoiceSettingsPanel({
  voices,
  selectedVoice,
  onSelectVoice,
  rate,
  onRateChange,
  onGenerate,
  isSubmitting,
}: VoiceSettingsPanelProps) {
  return (
    <div className="flex flex-col gap-6 rounded-xl border border-border bg-card p-5">
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-muted-foreground">Giọng đọc (Voice)</label>
        <select
          value={selectedVoice}
          onChange={(e) => onSelectVoice(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none"
        >
          {voices.map((v) => (
            <option key={v.voiceType} value={v.voiceType}>
              {v.displayName} ({v.languageCode})
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex justify-between text-xs font-semibold text-muted-foreground">
          <span>Tốc độ đọc (Speed)</span>
          <span className="text-foreground">{rate.toFixed(2)}x</span>
        </div>
        <input
          type="range"
          min="0.5"
          max="2.0"
          step="0.05"
          value={rate}
          onChange={(e) => onRateChange(parseFloat(e.target.value))}
          className="accent-primary"
        />
      </div>

      <button
        onClick={onGenerate}
        disabled={isSubmitting}
        className="mt-2 w-full rounded-lg bg-primary py-3 font-semibold text-primary-foreground shadow transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {isSubmitting ? "Creating audio..." : "Generate Speech"}
      </button>
    </div>
  )
}
```

Create `apps/web/src/components/tts/tts-studio.tsx`:
```tsx
"use client"
import { useState } from "react"
import { TextComposer } from "./text-composer"
import { VoiceSettingsPanel } from "./voice-settings-panel"
import { useVoices } from "@/hooks/use-voices"
import { useTTSJob } from "@/hooks/use-tts-job"
import { apiFetch } from "@/lib/api-client"
import { TTSJob } from "@/types/tts-job"

export function TTSStudio() {
  const [text, setText] = useState("")
  const [selectedVoice, setSelectedVoice] = useState("BV421_vivn_streaming")
  const [rate, setRate] = useState(1.0)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: voiceData } = useVoices("vi-VN")
  const { data: activeJob } = useTTSJob(activeJobId)

  const handleGenerate = async () => {
    if (!text.trim()) return
    setIsSubmitting(true)
    try {
      const job = await apiFetch<TTSJob>("/api/v1/tts/jobs", {
        method: "POST",
        body: JSON.stringify({
          text,
          voiceType: selectedVoice,
          rate,
        }),
      })
      setActiveJobId(job.id)
    } catch (err) {
      console.error("Job creation failed", err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="flex flex-col gap-6 lg:col-span-2">
        <TextComposer value={text} onChange={setText} maxLength={3000} />
        {activeJob && (
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="text-sm font-semibold">Job Status: {activeJob.status}</div>
            {activeJob.audioUrl && (
              <audio controls src={`http://localhost:8000${activeJob.audioUrl}`} className="mt-4 w-full" />
            )}
          </div>
        )}
      </div>
      <div>
        <VoiceSettingsPanel
          voices={voiceData?.items ?? []}
          selectedVoice={selectedVoice}
          onSelectVoice={setSelectedVoice}
          rate={rate}
          onRateChange={setRate}
          onGenerate={handleGenerate}
          isSubmitting={isSubmitting}
        />
      </div>
    </div>
  )
}
```

Update `apps/web/src/app/page.tsx`:
```tsx
import { PageContainer } from "@/components/app-shell/page-container"
import { TTSStudio } from "@/components/tts/tts-studio"

export default function HomePage() {
  return (
    <PageContainer>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Text to Speech Studio</h1>
        <p className="text-sm text-muted-foreground">Tạo giọng đọc tự nhiên từ văn bản</p>
      </div>
      <TTSStudio />
    </PageContainer>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/tts/ apps/web/src/app/page.tsx
git commit -m "feat(frontend): implement Text to Speech Studio page components"
```

---

### Task 12: Voice Library Catalog & Search Page

**Files:**
- Create: `apps/web/src/components/voices/voice-card.tsx`
- Create: `apps/web/src/app/voices/page.tsx`

**Interfaces:**
- Consumes: Catalog API `/api/v1/voices`.
- Produces: Interactive Voice Catalog Grid with filtering.

- [ ] **Step 1: Implement Voice Card component**

Create `apps/web/src/components/voices/voice-card.tsx`:
```tsx
"use client"
import { Voice } from "@/types/voice"

export function VoiceCard({ voice }: { voice: Voice }) {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-border bg-card p-5 shadow-sm transition-all hover:border-primary">
      <div>
        <div className="flex items-center justify-between">
          <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
            {voice.languageCode}
          </span>
        </div>
        <h3 className="mt-3 text-base font-bold">{voice.displayName}</h3>
        <p className="mt-1 font-mono text-xs text-muted-foreground">{voice.voiceType}</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Implement Voice Catalog Page**

Create `apps/web/src/app/voices/page.tsx`:
```tsx
"use client"
import { useState } from "react"
import { PageContainer } from "@/components/app-shell/page-container"
import { VoiceCard } from "@/components/voices/voice-card"
import { useVoices } from "@/hooks/use-voices"

export default function VoicesPage() {
  const [search, setSearch] = useState("")
  const { data, isLoading } = useVoices(undefined, search)

  return (
    <PageContainer>
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Voice Library</h1>
          <p className="text-sm text-muted-foreground">Khám phá và nghe thử các giọng đọc sẵn có</p>
        </div>
        <input
          type="text"
          placeholder="Tìm giọng đọc..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-border bg-card px-4 py-2 text-sm focus:outline-none"
        />
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading voices...</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((voice) => (
            <VoiceCard key={voice.voiceType} voice={voice} />
          ))}
        </div>
      )}
    </PageContainer>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/voices/ apps/web/src/app/voices/page.tsx
git commit -m "feat(frontend): implement Voice Library catalog search page"
```

---

### Task 13: Generation History & Management Page

**Files:**
- Create: `apps/web/src/app/history/page.tsx`
- Create: `apps/web/src/hooks/use-history.ts`

**Interfaces:**
- Consumes: Backend `/api/v1/tts/jobs` list endpoint.
- Produces: Generation history dashboard.

- [ ] **Step 1: Implement History data hook**

Create `apps/web/src/hooks/use-history.ts`:
```ts
import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api-client"
import { TTSJob } from "@/types/tts-job"

type HistoryResponse = {
  items: TTSJob[]
  page: number
  pageSize: number
  total: number
}

export function useHistory(page = 1) {
  return useQuery({
    queryKey: ["history", page],
    queryFn: () => apiFetch<HistoryResponse>(`/api/v1/tts/jobs?page=${page}`),
  })
}
```

- [ ] **Step 2: Implement History page layout**

Create `apps/web/src/app/history/page.tsx`:
```tsx
"use client"
import { PageContainer } from "@/components/app-shell/page-container"
import { useHistory } from "@/hooks/use-history"

export default function HistoryPage() {
  const { data, isLoading } = useHistory()

  return (
    <PageContainer>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Lịch sử tạo (History)</h1>
        <p className="text-sm text-muted-foreground">Quản lý các file âm thanh đã khởi tạo</p>
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading history...</div>
      ) : (
        <div className="flex flex-col gap-3">
          {data?.items.map((job) => (
            <div key={job.id} className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
              <div>
                <div className="font-semibold">{job.voiceDisplayName}</div>
                <div className="text-xs text-muted-foreground">{job.textPreview}</div>
              </div>
              <div className="text-xs font-semibold capitalize">{job.status}</div>
            </div>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/hooks/use-history.ts apps/web/src/app/history/page.tsx
git commit -m "feat(frontend): implement Generation History dashboard page"
```

---

### Task 14: Settings Page & Application Preferences

**Files:**
- Create: `apps/web/src/app/settings/page.tsx`

**Interfaces:**
- Consumes: Application state and `/api/v1/health`.
- Produces: Settings page interface.

- [ ] **Step 1: Implement Settings Page**

Create `apps/web/src/app/settings/page.tsx`:
```tsx
"use client"
import { PageContainer } from "@/components/app-shell/page-container"
import { useTheme } from "next-themes"

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()

  return (
    <PageContainer>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Cấu hình (Settings)</h1>
        <p className="text-sm text-muted-foreground">Cấu hình giao diện và tùy chọn mặc định</p>
      </div>

      <div className="max-w-xl space-y-6 rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-semibold">Giao diện (Theme)</div>
            <div className="text-xs text-muted-foreground">Tùy chọn hiển thị sáng / tối</div>
          </div>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm"
          >
            <option value="dark">Dark Studio</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>
    </PageContainer>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/app/settings/page.tsx
git commit -m "feat(frontend): implement Settings & Preferences page"
```

---

### Task 15: Full Verification & E2E Testing Suite

**Files:**
- Create: `apps/web/tests/e2e.spec.ts`

**Interfaces:**
- Consumes: Running Next.js and FastAPI servers.
- Produces: Automated E2E verification test suite.

- [ ] **Step 1: Write E2E test file**

Create `apps/web/tests/e2e.spec.ts`:
```ts
import { test, expect } from '@playwright/test'

test('should render homepage and allow text entry', async ({ page }) => {
  await page.goto('http://localhost:3000')
  await expect(page.locator('h1')).toContainText('Text to Speech Studio')
  const textarea = page.locator('textarea')
  await textarea.fill('Xin chào CapVoice Studio')
  await expect(textarea).toHaveValue('Xin chào CapVoice Studio')
})
```

- [ ] **Step 2: Run all backend tests**

Run: `PYTHONPATH=apps/api pytest apps/api/tests -v`
Expected: ALL PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/web/tests/e2e.spec.ts
git commit -m "test: add E2E Playwright test suite and pass all backend tests"
```

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-01-project-implementation.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach would you like to take?
