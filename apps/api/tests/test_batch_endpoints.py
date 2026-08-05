import pytest
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_create_batch_txt(monkeypatch):
    from app.workers.queue_manager import queue_manager
    from unittest.mock import AsyncMock
    enqueue_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(queue_manager, "enqueue", enqueue_mock)
    from app.providers.base import ProviderVoice
    dummy_voice = ProviderVoice(
        language_short="vi",
        language_code="vi-VN",
        voice_type="BV525_mix_kzn_hyenthu",
        display_name="BV525",
        resource_id="123",
        provider_id="capcut"
    )
    monkeypatch.setattr("app.api.v1.tts_batches.voice_catalog.get_voice", lambda x: dummy_voice)
    
    file_content = b"hello world\nsecond line\n\nthird line"
    response = client.post(
        "/api/v1/tts/batches",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        data={"voiceType": "BV525_mix_kzn_hyenthu", "rate": 1.0}
    )
    
    assert response.status_code == 202, response.text
    data = response.json()
    assert "batchId" in data
    assert len(data["jobs"]) == 3
    assert data["jobs"][0]["text"] == "hello world"
    assert data["jobs"][1]["text"] == "second line"
    assert data["jobs"][2]["text"] == "third line"
    
    # Should enqueue 3 jobs
    assert enqueue_mock.call_count == 3


@pytest.mark.asyncio
async def test_create_batch_csv(monkeypatch):
    from app.workers.queue_manager import queue_manager
    from unittest.mock import AsyncMock
    enqueue_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(queue_manager, "enqueue", enqueue_mock)
    from app.providers.base import ProviderVoice
    dummy_voice = ProviderVoice(
        language_short="vi",
        language_code="vi-VN",
        voice_type="BV525_mix_kzn_hyenthu",
        display_name="BV525",
        resource_id="123",
        provider_id="capcut"
    )
    monkeypatch.setattr("app.api.v1.tts_batches.voice_catalog.get_voice", lambda x: dummy_voice)
    
    file_content = b"id,text,other\n1,hello csv,ignore\n2,second csv,ignore"
    response = client.post(
        "/api/v1/tts/batches",
        files={"file": ("test.csv", io.BytesIO(file_content), "text/csv")},
        data={"voiceType": "BV525_mix_kzn_hyenthu", "rate": 1.0}
    )
    
    assert response.status_code == 202, response.text
    data = response.json()
    assert len(data["jobs"]) == 2
    assert data["jobs"][0]["text"] == "hello csv"
    assert data["jobs"][1]["text"] == "second csv"


@pytest.mark.asyncio
async def test_get_batch_status(monkeypatch, async_session):
    # First create a batch
    from app.workers.queue_manager import queue_manager
    from unittest.mock import AsyncMock
    enqueue_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(queue_manager, "enqueue", enqueue_mock)
    from app.providers.base import ProviderVoice
    dummy_voice = ProviderVoice(
        language_short="vi",
        language_code="vi-VN",
        voice_type="BV525_mix_kzn_hyenthu",
        display_name="BV525",
        resource_id="123",
        provider_id="capcut"
    )
    monkeypatch.setattr("app.api.v1.tts_batches.voice_catalog.get_voice", lambda x: dummy_voice)
    
    file_content = b"line 1\nline 2"
    create_resp = client.post(
        "/api/v1/tts/batches",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        data={"voiceType": "BV525_mix_kzn_hyenthu", "rate": 1.0}
    )
    batch_id = create_resp.json()["batchId"]
    
    # Now get status
    status_resp = client.get(f"/api/v1/tts/batches/{batch_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["batchId"] == batch_id
    assert data["totalJobs"] == 2
    assert data["pendingJobs"] == 2
    assert data["completedJobs"] == 0
    assert data["progress"] == 0.0

@pytest.mark.asyncio
async def test_download_batch_no_completed(monkeypatch, async_session):
    # If no jobs are completed, should return 400
    from app.workers.queue_manager import queue_manager
    from unittest.mock import AsyncMock
    enqueue_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(queue_manager, "enqueue", enqueue_mock)
    from app.providers.base import ProviderVoice
    dummy_voice = ProviderVoice(
        language_short="vi",
        language_code="vi-VN",
        voice_type="BV525_mix_kzn_hyenthu",
        display_name="BV525",
        resource_id="123",
        provider_id="capcut"
    )
    monkeypatch.setattr("app.api.v1.tts_batches.voice_catalog.get_voice", lambda x: dummy_voice)
    
    file_content = b"line 1\nline 2"
    create_resp = client.post(
        "/api/v1/tts/batches",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        data={"voiceType": "BV525_mix_kzn_hyenthu", "rate": 1.0}
    )
    batch_id = create_resp.json()["batchId"]
    
    dl_resp = client.get(f"/api/v1/tts/batches/{batch_id}/download")
    assert dl_resp.status_code == 400
    assert dl_resp.json()["detail"] == "NO_COMPLETED_JOBS_IN_BATCH"
