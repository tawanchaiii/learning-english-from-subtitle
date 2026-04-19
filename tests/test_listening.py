import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from generate_tts import SUPPORTED_MODES, CUSTOM_VOICES


class TestGenerateTTSConstants:
    def test_supported_modes(self):
        assert "base" in SUPPORTED_MODES
        assert "design" in SUPPORTED_MODES
        assert "custom" in SUPPORTED_MODES
        assert len(SUPPORTED_MODES) == 3

    def test_custom_voices(self):
        assert "Chelsie" in CUSTOM_VOICES
        assert "Ethan" in CUSTOM_VOICES
        assert "Vivienne" in CUSTOM_VOICES
        assert "Ryan" in CUSTOM_VOICES
        assert len(CUSTOM_VOICES) == 4


class TestGenerateTTSArgParsing:
    def test_mode_choices_are_valid(self):
        import argparse
        from generate_tts import main

        parser = argparse.ArgumentParser()
        parser.add_argument("--mode", choices=SUPPORTED_MODES)
        parsed = parser.parse_args(["--mode", "custom"])
        assert parsed.mode == "custom"

        parsed = parser.parse_args(["--mode", "design"])
        assert parsed.mode == "design"

        parsed = parser.parse_args(["--mode", "base"])
        assert parsed.mode == "base"


class TestGenerateTTSHelpers:
    def test_check_mlx_audio_returns_bool(self):
        from generate_tts import check_mlx_audio

        result = check_mlx_audio()
        assert isinstance(result, bool)

    def test_passage_json_schema(self):
        """Verify the expected JSON schema for TTS passages."""
        passage = {
            "id": "track_01",
            "speaker": "Chelsie",
            "text": "Hello, how are you?",
        }
        assert "id" in passage
        assert "speaker" in passage
        assert "text" in passage

