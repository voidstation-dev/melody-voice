"""Tests for the ProviderRegistry."""

from app.providers.registry import (
    CAPCUT,
    VIENEU,
    ProviderRegistry,
    provider_registry,
)


def test_default_provider_is_capcut():
    assert provider_registry.default_provider_id == CAPCUT


def test_known_providers_registered():
    assert provider_registry.is_known(CAPCUT)
    assert provider_registry.is_known(VIENEU)
    assert not provider_registry.is_known("bogus")


def test_capcut_descriptor_shape():
    desc = provider_registry.get_descriptor(CAPCUT)
    assert desc is not None
    assert desc.id == CAPCUT
    assert desc.label == "CapCut"
    # CapCut legacy: no cloning, no streaming, no styles.
    assert desc.capabilities.supports_preset_voices is True
    assert desc.capabilities.supports_voice_cloning is False


def test_vieneu_descriptor_from_core():
    desc = provider_registry.get_descriptor(VIENEU)
    assert desc is not None
    assert desc.id == VIENEU
    assert desc.label == "VieNeu"
    # VieNeu v3 Turbo capabilities (from vieneu-core default_descriptor).
    assert desc.capabilities.supports_voice_cloning is True
    assert desc.capabilities.supports_streaming is True
    assert desc.capabilities.sample_rate == 48000


def test_list_providers_returns_both():
    providers = provider_registry.list_providers()
    ids = {p.id for p in providers}
    assert ids == {CAPCUT, VIENEU}


def test_empty_registry_is_safe():
    reg = ProviderRegistry()
    assert reg.default_provider_id == CAPCUT
    assert reg.get_descriptor(CAPCUT) is None
    assert reg.list_providers() == []