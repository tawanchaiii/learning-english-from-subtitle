"""Parse .srt and .vtt subtitle files into structured JSON."""

import json
import os
import re
import sys

SCENE_GAP_SECONDS = 5.0


def _time_to_seconds(time_str: str) -> float:
    """Convert timestamp string to seconds.

    Handles both SRT format (HH:MM:SS,mmm) and VTT format (HH:MM:SS.mmm).
    """
    time_str = time_str.strip().replace(",", ".")
    parts = time_str.split(":")
    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def _parse_srt(content: str) -> list[dict]:
    """Parse SRT content into a list of subtitle entries."""
    blocks = re.split(r"\n\s*\n", content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        try:
            index = int(lines[0].strip())
        except ValueError:
            continue
        timestamp_match = re.match(
            r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})",
            lines[1].strip(),
        )
        if not timestamp_match:
            continue
        start_time = timestamp_match.group(1)
        end_time = timestamp_match.group(2)
        text = " ".join(line.strip() for line in lines[2:])
        entries.append(
            {
                "index": index,
                "start_time": start_time,
                "end_time": end_time,
                "start_seconds": _time_to_seconds(start_time),
                "end_seconds": _time_to_seconds(end_time),
                "text": text,
            }
        )
    return entries


def _parse_vtt(content: str) -> list[dict]:
    """Parse VTT (WebVTT) content into a list of subtitle entries."""
    lines_raw = content.strip().split("\n")
    start_idx = 0
    for i, line in enumerate(lines_raw):
        if line.strip().upper().startswith("WEBVTT"):
            start_idx = i + 1
            break
    content = "\n".join(lines_raw[start_idx:])

    blocks = re.split(r"\n\s*\n", content.strip())
    entries = []
    index = 0
    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue
        timestamp_line_idx = None
        for i, line in enumerate(lines):
            if "-->" in line:
                timestamp_line_idx = i
                break
        if timestamp_line_idx is None:
            continue
        timestamp_match = re.match(
            r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})",
            lines[timestamp_line_idx].strip(),
        )
        if not timestamp_match:
            continue
        index += 1
        start_time = timestamp_match.group(1)
        end_time = timestamp_match.group(2)
        text = " ".join(
            line.strip() for line in lines[timestamp_line_idx + 1 :] if line.strip()
        )
        entries.append(
            {
                "index": index,
                "start_time": start_time,
                "end_time": end_time,
                "start_seconds": _time_to_seconds(start_time),
                "end_seconds": _time_to_seconds(end_time),
                "text": text,
            }
        )
    return entries


def _group_into_scenes(entries: list[dict]) -> list[dict]:
    """Group subtitle entries into scenes based on time gaps."""
    if not entries:
        return []
    scenes = []
    current_scene_lines = [entries[0]]
    for i in range(1, len(entries)):
        prev_end = entries[i - 1]["end_seconds"]
        curr_start = entries[i]["start_seconds"]
        if curr_start - prev_end > SCENE_GAP_SECONDS:
            scenes.append(current_scene_lines)
            current_scene_lines = [entries[i]]
        else:
            current_scene_lines.append(entries[i])
    scenes.append(current_scene_lines)

    result = []
    for idx, scene_lines in enumerate(scenes):
        result.append(
            {
                "scene_id": f"scene_{idx + 1}",
                "start_time": scene_lines[0]["start_time"],
                "end_time": scene_lines[-1]["end_time"],
                "lines": [
                    {
                        "index": line["index"],
                        "start_time": line["start_time"],
                        "end_time": line["end_time"],
                        "text": line["text"],
                    }
                    for line in scene_lines
                ],
            }
        )
    return result


def parse_subtitle(filepath: str) -> dict:
    """Parse a subtitle file and return structured data.

    Args:
        filepath: Path to .srt or .vtt file.

    Returns:
        Dict with movie_name, format, scenes, and metadata.
    """
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in (".srt", ".vtt"):
        raise ValueError(f"Unsupported subtitle format: {ext}. Use .srt or .vtt")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if ext == ".srt":
        entries = _parse_srt(content)
    elif ext == ".vtt":
        entries = _parse_vtt(content)

    scenes = _group_into_scenes(entries)

    return {
        "filename": filename,
        "movie_name": name,
        "format": ext.lstrip("."),
        "total_lines": len(entries),
        "scenes": scenes,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_subtitle.py <subtitle-file>")
        sys.exit(1)
    result = parse_subtitle(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
