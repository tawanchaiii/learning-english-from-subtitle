"""Generate exercise-data.json and vocab-data.json from a guideline JSON."""

import json
import re
import sys
from collections import Counter


def parse_choice(choice_str):
    m = re.match(r"^([A-E])\)\s*(.+)$", choice_str.strip())
    if m:
        return {"label": m.group(1), "text": m.group(2)}
    return {"label": choice_str[0], "text": choice_str[3:]}


def generate_exercise_data(guideline):
    part_a_questions = []
    for q in guideline["parts"]["A"]["questions"]:
        part_a_questions.append(
            {
                "id": q["id"],
                "points": 2,
                "prompt": q["prompt"],
                "choices": [parse_choice(c) for c in q["choices"]],
            }
        )

    part_b_questions = []
    for q in guideline["parts"]["B"]["questions"]:
        part_b_questions.append(
            {
                "id": q["id"],
                "points": 2,
                "prompt": q["prompt"],
                "choices": [parse_choice(c) for c in q["choices"]],
            }
        )

    box_heights = {
        "scene_summary": "6cm",
        "character_intent": "6cm",
        "alternative_dialogue": "7cm",
        "vocabulary_sentence": "5cm",
    }

    part_c_questions = []
    for i, q in enumerate(guideline["parts"]["C"]["questions"]):
        needs_newpage = i > 0 and i % 2 == 0
        part_c_questions.append(
            {
                "id": q["id"],
                "points": q.get("rubric", {}).get("max_score", 10),
                "prompt": q["prompt"],
                "box_height": box_heights.get(q["type"], "6cm"),
                "needs_newpage": needs_newpage,
            }
        )

    part_a_pts = sum(q["points"] for q in part_a_questions)
    part_b_pts = sum(q["points"] for q in part_b_questions)
    part_c_pts = sum(q["points"] for q in part_c_questions)
    total_pts = part_a_pts + part_b_pts + part_c_pts

    return {
        "doc_type": "Exercise",
        "movie_name": guideline["movie"],
        "cefr_level": guideline["learner_cefr"],
        "detected_cefr": guideline["detected_cefr"],
        "learner_cefr": guideline["learner_cefr"],
        "generated_date": guideline["generated_date"],
        "total_points": total_pts,
        "parts": [
            {"label": "A", "points": part_a_pts},
            {"label": "B", "points": part_b_pts},
            {"label": "C", "points": part_c_pts},
        ],
        "part_a_points": part_a_pts,
        "part_a_questions": part_a_questions,
        "part_b_points": part_b_pts,
        "part_b_questions": part_b_questions,
        "part_b_needs_newpage": True,
        "part_c_points": part_c_pts,
        "part_c_questions": part_c_questions,
    }


def generate_vocab_data(guideline):
    vocab_list = guideline["vocabulary_list"]
    cefr_order = ["A2", "B1", "B2"]
    cefr_descriptions = {
        "A2": "Elementary — Basic everyday expressions",
        "B1": "Intermediate — Frequently used vocabulary",
        "B2": "Upper Intermediate — More complex expressions",
    }

    by_level = {}
    for w in vocab_list:
        level = w["cefr"]
        by_level.setdefault(level, []).append(w)

    cefr_levels = []
    cefr_sections = []
    priority_words = []

    for level in cefr_order:
        words = by_level.get(level, [])
        if not words:
            continue
        cefr_levels.append({"name": level, "count": len(words)})
        cefr_sections.append(
            {
                "name": level,
                "description": cefr_descriptions.get(level, ""),
                "count": len(words),
                "words": [
                    {
                        "word": w["word"],
                        "pos": w["part_of_speech"],
                        "meaning": w["meaning"],
                        "movie_example": w["movie_example"],
                        "real_life_example": w["real_life_example"],
                    }
                    for w in words
                ],
            }
        )

    for level in cefr_order:
        if level == guideline["learner_cefr"]:
            for w in by_level.get(level, []):
                priority_words.append(w["word"])

    return {
        "doc_type": "Vocabulary List",
        "movie_name": guideline["movie"],
        "cefr_level": guideline["learner_cefr"],
        "detected_cefr": guideline["detected_cefr"],
        "learner_cefr": guideline["learner_cefr"],
        "generated_date": guideline["generated_date"],
        "total_words": len(vocab_list),
        "cefr_levels": cefr_levels,
        "priority_words": priority_words,
        "cefr_sections": cefr_sections,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_data.py <guideline.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        guideline = json.load(f)

    base = sys.argv[1].replace("-guideline.json", "")
    dir_path = "/".join(base.split("/")[:-1]) if "/" in base else "."
    name = base.split("/")[-1] if "/" in base else base.replace("-guideline.json", "")

    exercise_data = generate_exercise_data(guideline)
    exercise_path = f"{base}-exercise-data.json"
    with open(exercise_path, "w", encoding="utf-8") as f:
        json.dump(exercise_data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {exercise_path}")

    vocab_data = generate_vocab_data(guideline)
    vocab_path = f"{base}-vocab-data.json"
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {vocab_path}")
