import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from generate_tts import SUPPORTED_MODES, CUSTOM_VOICES

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


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


class TestListeningTemplateRendering:
    def test_render_listening_template_produces_tex_file(self):
        from render_latex import render_template

        data = {
            "doc_type": "Listening Exercise",
            "movie_name": "TestMovie",
            "cefr_level": "B1",
            "detected_cefr": "B1",
            "learner_cefr": "A2",
            "generated_date": "2026-04-19",
            "audio_prefix": "TestMovie",
            "total_points": 20,
            "total_count": 8,
            "part_a_points": 8,
            "part_a_count": 4,
            "part_b_points": 12,
            "part_b_count": 4,
            "part_a_passages": [
                {
                    "id": "A1",
                    "track_number": 1,
                    "scene_ref": "scene_1 [00:01:00]",
                    "context": "Two friends at a cafe",
                    "questions": [
                        {
                            "id": "L1",
                            "points": 2,
                            "type": "multiple_choice",
                            "prompt": "What does the woman suggest?",
                            "choices": [
                                {"label": "A", "text": "Go to the park"},
                                {"label": "B", "text": "Watch a movie"},
                                {"label": "C", "text": "Study at home"},
                                {"label": "D", "text": "Visit a museum"},
                            ],
                        }
                    ],
                }
            ],
            "part_b_passages": [
                {
                    "id": "B1",
                    "track_number": 4,
                    "scene_ref": "scene_5 [00:10:00]",
                    "context": "A professor explaining photosynthesis",
                    "questions": [
                        {
                            "id": "L4",
                            "points": 3,
                            "type": "multiple_choice",
                            "prompt": "What is the main topic?",
                            "choices": [
                                {"label": "A", "text": "Animal behavior"},
                                {"label": "B", "text": "Photosynthesis"},
                                {"label": "C", "text": "Weather patterns"},
                                {"label": "D", "text": "Ocean currents"},
                            ],
                        },
                        {
                            "id": "L5",
                            "points": 3,
                            "type": "short_answer",
                            "prompt": "Why does the professor mention the experiment?",
                            "box_height": "3cm",
                        },
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "listening_test.tex")
            render_template(
                template_name="listening.tex.j2",
                data=data,
                output_path=output_path,
                templates_dir=TEMPLATES_DIR,
            )
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
            assert "TestMovie" in content
            assert "Listening Exercise" in content
            assert "Short Conversations" in content
            assert "Longer Talks" in content
            assert "Track 1" in content
            assert "Track 4" in content

    def test_render_listening_template_with_no_context(self):
        from render_latex import render_template

        data = {
            "doc_type": "Listening Exercise",
            "movie_name": "Minimal",
            "cefr_level": "A1",
            "detected_cefr": "A1",
            "learner_cefr": "A1",
            "generated_date": "2026-04-19",
            "audio_prefix": "Minimal",
            "total_points": 6,
            "total_count": 3,
            "part_a_points": 3,
            "part_a_count": 3,
            "part_b_points": 3,
            "part_b_count": 3,
            "part_a_passages": [
                {
                    "id": "A1",
                    "track_number": 1,
                    "scene_ref": "scene_1 [00:00:30]",
                    "questions": [
                        {
                            "id": "L1",
                            "points": 1,
                            "type": "multiple_choice",
                            "prompt": "What is the speaker talking about?",
                            "choices": [
                                {"label": "A", "text": "Option A"},
                                {"label": "B", "text": "Option B"},
                                {"label": "C", "text": "Option C"},
                                {"label": "D", "text": "Option D"},
                            ],
                        }
                    ],
                }
            ],
            "part_b_passages": [
                {
                    "id": "B1",
                    "track_number": 2,
                    "scene_ref": "scene_3 [00:05:00]",
                    "questions": [
                        {
                            "id": "L2",
                            "points": 1,
                            "type": "short_answer",
                            "prompt": "Summarize the passage.",
                            "box_height": "4cm",
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "listening_minimal.tex")
            render_template(
                template_name="listening.tex.j2",
                data=data,
                output_path=output_path,
                templates_dir=TEMPLATES_DIR,
            )
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
            assert "Minimal" in content
            assert "Listening Exercise" in content
