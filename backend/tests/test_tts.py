import base64
import os
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.tts import get_cache_path, is_cached, synthesize

client = TestClient(app)

def test_tts_cache_hit_makes_no_network_call(tmp_path):
    text = "चाचणी ऑडिओ कॅश संदेश"
    lang = "mr"
    cache_path = get_cache_path(text, lang)
    dummy_wav = b"RIFFDUMMYWAVEDATA"
    cache_path.write_bytes(dummy_wav)

    try:
        with patch("src.tts.httpx.Client") as mock_client_cls:
            audio = synthesize(text, lang)
            assert audio == dummy_wav
            mock_client_cls.assert_not_called()
    finally:
        if cache_path.exists():
            cache_path.unlink()

def test_tts_endpoint_returns_audio_and_cached_header():
    text = "कॅश केलेला ऑडिओ चाचणी"
    lang = "mr"
    cache_path = get_cache_path(text, lang)
    dummy_wav = b"RIFFCACHEDWAVEENDPOINT"
    cache_path.write_bytes(dummy_wav)

    try:
        res = client.post("/api/tts", json={"text": text, "lang": lang})
        assert res.status_code == 200
        assert res.content == dummy_wav
        assert res.headers.get("X-TTS-Source") == "cached"
    finally:
        if cache_path.exists():
            cache_path.unlink()

def test_tts_offline_mode_never_calls_network(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "offline")
    text = "Non-cached text for offline mode test 12345"
    lang = "hi"
    cache_path = get_cache_path(text, lang)
    if cache_path.exists():
        cache_path.unlink()

    with patch("src.tts.httpx.Client") as mock_client_cls:
        audio = synthesize(text, lang)
        assert audio is None
        mock_client_cls.assert_not_called()

    # Endpoint returns 204 in offline mode when not cached
    res = client.post("/api/tts", json={"text": text, "lang": lang})
    assert res.status_code == 204

def test_tts_api_error_returns_204(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "live")
    monkeypatch.setenv("SARVAM_API_KEY", "dummy_key")
    text = "Uncached text triggering api error 67890"
    lang = "en"
    cache_path = get_cache_path(text, lang)
    if cache_path.exists():
        cache_path.unlink()

    with patch("src.tts.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.post.side_effect = Exception("Sarvam network timeout")
        mock_client_cls.return_value.__enter__.return_value = mock_instance

        res = client.post("/api/tts", json={"text": text, "lang": lang})
        assert res.status_code == 204

def test_tts_missing_key_returns_204(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "live")
    monkeypatch.setenv("SARVAM_API_KEY", "")
    text = "Uncached text without api key 99999"
    lang = "mr"
    cache_path = get_cache_path(text, lang)
    if cache_path.exists():
        cache_path.unlink()

    res = client.post("/api/tts", json={"text": text, "lang": lang})
    assert res.status_code == 204
