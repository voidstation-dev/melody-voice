from pathlib import Path

import pytest

from app.providers.capcut_provider import CapCutProvider


@pytest.mark.asyncio
async def test_list_voices_from_dummy_catalog(tmp_path: Path):
    catalog_file = tmp_path / "Voice.json"
    catalog_file.write_text(
        '[{"lan": "vi", "lang": "vi-VN", "voice_type": "BV421_vivn_streaming", "display_name": "Nhỏ Ngọt Ngào", "resource_id": "7252594014782755330"}]',
        encoding="utf-8",
    )

    provider = CapCutProvider(catalog_path=catalog_file)
    voices = await provider.list_voices()

    assert len(voices) >= 1
    assert any(v.voice_type == "BV421_vivn_streaming" for v in voices)
    assert voices[0].display_name == "Nhỏ Ngọt Ngào"
    assert voices[0].voice_type == "BV421_vivn_streaming"
    assert voices[0].language_code == "vi-VN"


class FakeCapCutClient:
    def __init__(self):
        self.calls = []

    def generate_speech(self, **kwargs):
        self.calls.append(kwargs)
        return {"data": {"audio_url": "https://cdn.example/audio.mp3"}}


@pytest.mark.asyncio
async def test_provider_reuses_client_and_uses_configured_timeout(tmp_path: Path):
    client = FakeCapCutClient()
    factory_calls = 0

    def client_factory(device):
        nonlocal factory_calls
        factory_calls += 1
        return client

    provider = CapCutProvider(
        catalog_path=tmp_path / "Voice.json",
        timeout_seconds=17,
        client_factory=client_factory,
    )

    await provider.synthesize(
        text="one",
        voice_type="voice",
        resource_id="resource",
        rate=1.0,
    )
    await provider.synthesize(
        text="two",
        voice_type="voice",
        resource_id="resource",
        rate=1.0,
    )

    assert factory_calls == 1
    assert len(client.calls) == 2
    assert [call["timeout"] for call in client.calls] == [17, 17]
