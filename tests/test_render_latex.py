import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from render_latex import render_template

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def test_render_template_produces_tex_file():
    data = {
        "doc_type": "Exercise",
        "movie_name": "TestMovie",
        "cefr_level": "B1",
        "detected_cefr": "B1",
        "learner_cefr": "A2",
        "generated_date": "2026-04-16",
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


def test_render_template_substitutes_variables():
    data = {
        "doc_type": "Vocabulary List",
        "movie_name": "Frozen",
        "cefr_level": "A2",
        "detected_cefr": "A2",
        "learner_cefr": "A1",
        "generated_date": "2026-04-16",
        "total_words": 50,
        "cefr_levels": [],
        "priority_words": [],
        "cefr_sections": [],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "vocab.tex")
        render_template(
            template_name="vocabulary.tex.j2",
            data=data,
            output_path=output_path,
            templates_dir=TEMPLATES_DIR,
        )
        with open(output_path, "r") as f:
            content = f.read()
        assert "Frozen" in content
        assert "Vocabulary List" in content
