import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from parse_subtitle import parse_subtitle


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parse_srt_returns_dict_with_required_keys():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.srt"))
    assert "filename" in result
    assert "movie_name" in result
    assert "format" in result
    assert "total_lines" in result
    assert "scenes" in result


def test_parse_srt_extracts_movie_name():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.srt"))
    assert result["movie_name"] == "sample"
    assert result["format"] == "srt"


def test_parse_srt_groups_scenes_by_time_gap():
    """Lines with >5 second gap between them should be in different scenes."""
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.srt"))
    assert len(result["scenes"]) == 4


def test_parse_srt_scene_structure():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.srt"))
    scene = result["scenes"][0]
    assert "scene_id" in scene
    assert "start_time" in scene
    assert "end_time" in scene
    assert "lines" in scene
    assert len(scene["lines"]) == 3


def test_parse_srt_line_structure():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.srt"))
    line = result["scenes"][0]["lines"][0]
    assert "index" in line
    assert "start_time" in line
    assert "end_time" in line
    assert "text" in line
    assert line["text"] == "Jack, you're crazy!"


def test_parse_srt_total_lines():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.srt"))
    assert result["total_lines"] == 8
