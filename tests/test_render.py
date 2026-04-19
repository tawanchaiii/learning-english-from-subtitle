import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from render import render_template, escape_typst, escape_latex

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


class TestEscapeFilters:
    def test_escape_typst_brackets(self):
        assert escape_typst("hello [world]") == r"hello \[world\]"

    def test_escape_typst_hash(self):
        assert escape_typst("item #1") == r"item \#1"

    def test_escape_typst_backslash(self):
        assert escape_typst(r"path\file") == r"path\\file"

    def test_escape_typst_none(self):
        assert escape_typst(None) == ""

    def test_escape_typst_non_string(self):
        assert escape_typst(42) == "42"

    def test_escape_latex_special_chars(self):
        result = escape_latex("price $5 & 10% off #1")
        assert r"\$" in result
        assert r"\&" in result
        assert r"\%" in result
        assert r"\#" in result

    def test_escape_latex_none(self):
        assert escape_latex(None) == ""


class TestExerciseTypRendering:
    def test_render_exercise_typ(self):
        data = {
            "doc_type": "Exercise",
            "movie_name": "TestMovie",
            "cefr_level": "B1",
            "detected_cefr": "B1",
            "learner_cefr": "A2",
            "generated_date": "2026-04-19",
            "total_points": 65,
            "parts": [
                {"label": "A", "points": 30},
                {"label": "B", "points": 20},
                {"label": "C", "points": 15},
            ],
            "part_a_points": 30,
            "part_a_questions": [
                {
                    "id": "A1",
                    "points": 2,
                    "prompt": "What does 'bow' mean?",
                    "choices": [
                        {"label": "A", "text": "front part of a ship"},
                        {"label": "B", "text": "a weapon"},
                        {"label": "C", "text": "to bend"},
                        {"label": "D", "text": "a knot"},
                        {"label": "E", "text": "a type of tie"},
                    ],
                }
            ],
            "part_b_points": 20,
            "part_b_questions": [
                {
                    "id": "B1",
                    "points": 2,
                    "prompt": "What did Jack mean?",
                    "choices": [
                        {"label": "A", "text": "He was happy"},
                        {"label": "B", "text": "He was sad"},
                        {"label": "C", "text": "He was angry"},
                        {"label": "D", "text": "He was confused"},
                        {"label": "E", "text": "He was tired"},
                    ],
                }
            ],
            "part_b_needs_newpage": True,
            "part_c_points": 15,
            "part_c_questions": [
                {
                    "id": "C1",
                    "points": 10,
                    "prompt": "Summarize the scene",
                    "box_height": "4cm",
                    "needs_newpage": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.typ")
            render_template(
                template_name="exercise.typ.j2",
                data=data,
                output_path=output_path,
                templates_dir=TEMPLATES_DIR,
            )
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
            assert "TestMovie" in content
            assert "Part A" in content
            assert "Part B" in content
            assert "Part C" in content


class TestVocabularyTypRendering:
    def test_render_vocabulary_typ(self):
        data = {
            "doc_type": "Vocabulary List",
            "movie_name": "Frozen",
            "cefr_level": "A2",
            "detected_cefr": "A2",
            "learner_cefr": "A1",
            "generated_date": "2026-04-19",
            "total_words": 50,
            "cefr_levels": [
                {"name": "A1", "count": 10},
                {"name": "A2", "count": 20},
                {"name": "B1", "count": 20},
            ],
            "priority_words": ["let", "go", "frozen", "kingdom", "ice"],
            "cefr_sections": [
                {
                    "name": "A1",
                    "description": "Beginner",
                    "count": 10,
                    "words": [
                        {
                            "word": "go",
                            "pos": "verb",
                            "meaning": "to move",
                            "movie_example": "Let it go!",
                            "real_life_example": "I go to school every day.",
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "vocab.typ")
            render_template(
                template_name="vocabulary.typ.j2",
                data=data,
                output_path=output_path,
                templates_dir=TEMPLATES_DIR,
            )
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
            assert "Frozen" in content
            assert "Vocabulary List" in content


class TestAssessmentTypRendering:
    def test_render_assessment_typ(self):
        data = {
            "doc_type": "Assessment Report",
            "movie_name": "Titanic",
            "cefr_level": "B1",
            "learner_cefr": "B1",
            "assessment_date": "2026-04-19",
            "overall_score": 45,
            "overall_total": 65,
            "overall_percent": 69,
            "score_parts": [
                {"label": "A", "score": 25, "total": 30},
                {"label": "B", "score": 15, "total": 20},
                {"label": "C", "score": 5, "total": 15},
            ],
            "part_a_score": 25,
            "part_a_total": 30,
            "part_a_results": [
                {
                    "id": "A1",
                    "prompt": "What does bow mean?",
                    "learner_answer": "C",
                    "correct_answer": "C",
                    "is_correct": True,
                    "explanation": "Correct",
                }
            ],
            "part_b_score": 15,
            "part_b_total": 20,
            "part_b_results": [],
            "part_c_score": 5,
            "part_c_total": 15,
            "part_c_results": [
                {
                    "id": "C1",
                    "score": 5,
                    "max_score": 10,
                    "prompt": "Summarize the scene",
                    "learner_answer": "Jack and Rose are on the ship",
                    "criteria_scores": [
                        {
                            "name": "content_accuracy",
                            "score": 2,
                            "max": 3,
                            "feedback": "Good",
                        }
                    ],
                    "corrections": [],
                    "strengths": ["Mentions characters"],
                }
            ],
            "estimated_cefr": "B1",
            "cefr_comparison": "matches",
            "skill_breakdown": [
                {"name": "Vocabulary", "level": "B1", "assessment": "Good range"},
                {"name": "Grammar", "level": "A2", "assessment": "Needs work"},
            ],
            "weak_areas": [{"topic": "Grammar", "detail": "Verb tenses"}],
            "recommendations": ["Practice past tenses"],
            "suggested_movies": [
                {"title": "Forrest Gump", "cefr": "B1", "reason": "Clear dialogue"}
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "assessment.typ")
            render_template(
                template_name="assessment.typ.j2",
                data=data,
                output_path=output_path,
                templates_dir=TEMPLATES_DIR,
            )
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
            assert "Titanic" in content
            assert "Assessment Report" in content


class TestListeningTypRendering:
    def test_render_listening_typ(self):
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
            output_path = os.path.join(tmpdir, "listening_test.typ")
            render_template(
                template_name="listening.typ.j2",
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

    def test_render_listening_typ_no_context(self):
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
            output_path = os.path.join(tmpdir, "listening_minimal.typ")
            render_template(
                template_name="listening.typ.j2",
                data=data,
                output_path=output_path,
                templates_dir=TEMPLATES_DIR,
            )
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
            assert "Minimal" in content
            assert "Listening Exercise" in content


class TestLegacyLatexRendering:
    def test_render_exercise_tex_still_works(self):
        data = {
            "doc_type": "Exercise",
            "movie_name": "TestMovie",
            "cefr_level": "B1",
            "detected_cefr": "B1",
            "learner_cefr": "A2",
            "generated_date": "2026-04-19",
            "total_points": 65,
            "parts": [
                {"label": "A", "points": 30},
                {"label": "B", "points": 20},
                {"label": "C", "points": 15},
            ],
            "part_a_points": 30,
            "part_a_questions": [],
            "part_b_points": 20,
            "part_b_questions": [],
            "part_b_needs_newpage": True,
            "part_c_points": 15,
            "part_c_questions": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.tex")
            render_template(
                template_name="exercise.tex.j2",
                data=data,
                output_path=output_path,
                templates_dir=TEMPLATES_DIR,
            )
            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                content = f.read()
            assert "TestMovie" in content
            assert "\\documentclass" in content
