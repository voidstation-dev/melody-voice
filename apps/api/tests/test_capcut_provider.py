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
