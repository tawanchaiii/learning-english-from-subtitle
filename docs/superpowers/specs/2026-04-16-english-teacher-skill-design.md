# English Teacher Agent Skill — Design Spec

**Date:** 2026-04-16
**Status:** Draft
**Author:** Brainstorming session with user

---

## 1. Overview

A Claude Code agent skill called `english-teacher` that helps English learners practice by generating exercises from movie subtitles and assessing completed exercises. The skill has two modes:

- **`generate`** — Parse a subtitle file, generate exercises, vocabulary list, and answer guidelines
- **`assess`** — Read a scanned completed exercise PDF, score it, and produce a full learning report

### Invocation

```
/english-teacher generate <subtitle-file> --level <CEFR-level>
/english-teacher assess <movie-folder> <scanned-pdf>
```

### Examples

```
/english-teacher generate ./Titanic.srt --level A2
/english-teacher assess ./output/Titanic ./Titanic-completed.pdf
```

The movie name is derived by stripping the file extension from the subtitle filename. All output goes into `output/<movie-name>/`.

---

## 2. Dependencies

| Dependency | Purpose |
|---|---|
| `xelatex` (TeX Live) | PDF generation with Unicode support |
| `python3` + `jinja2` | LaTeX template rendering |
| docling-mcp | Reading scanned exercise PDFs during assessment |

The skill checks prerequisites on first run and provides install instructions if anything is missing.

---

## 3. Project Structure

```
learning-english-from-subtitle/
├── .claude/
│   └── skills/
│       └── english-teacher.md          # Agent skill definition
├── templates/
│   ├── common.tex.j2                   # Shared preamble: packages, fonts, header/footer
│   ├── exercise.tex.j2                 # Exercise layout (includes common.tex.j2)
│   ├── vocabulary.tex.j2              # Vocabulary table layout (includes common.tex.j2)
│   └── assessment.tex.j2             # Assessment report layout (includes common.tex.j2)
├── scripts/
│   ├── parse_subtitle.py              # Parse .srt/.vtt → structured JSON
│   ├── render_latex.py                # Render Jinja2 templates → .tex files
│   └── compile_pdf.sh                 # Compile .tex → .pdf via xelatex
├── output/                            # Generated exercise folders
│   └── <movie-name>/
│       ├── <movie-name>-exercise.pdf
│       ├── <movie-name>-vocabulary.pdf
│       ├── <movie-name>-guideline.json
│       ├── <movie-name>-assessment.pdf   # After assessment
│       └── <movie-name>-assessment.md    # After assessment
└── CLAUDE.md
```

---

## 4. Generate Mode

### 4.1 Subtitle Parsing

`parse_subtitle.py` accepts `.srt` and `.vtt` formats and produces structured JSON:

- Extracts: timestamps, speaker labels (if present), dialogue text
- Groups dialogues into scenes based on time gaps (>5 seconds gap = new scene)
- Output: `scenes.json` with scenes, lines, and metadata

### 4.2 Movie Difficulty Auto-Detection

The agent analyzes subtitle content to determine the movie's CEFR level by checking:

- Average sentence length and complexity
- Vocabulary frequency (common vs. rare words)
- Idiom/slang density
- Grammar structure complexity

### 4.3 Learner Level Adjustment

The learner specifies their CEFR level via `--level` flag (A1/A2/B1/B2/C1/C2). The agent combines the auto-detected movie level with the learner's level to:

- Adjust question difficulty
- Select appropriate vocabulary
- Calibrate rubric expectations for subjective questions

### 4.4 Exercise Generation Flow

```
Subtitle file (.srt/.vtt)
  → parse_subtitle.py → scenes.json
  → Agent selects key scenes, dialogues, vocabulary
  → Agent adjusts to learner's specified CEFR level
  → render_latex.py fills exercise.tex.j2
  → compile_pdf.sh → <movie-name>-exercise.pdf
```

### 4.5 Exercise PDF Structure

**Cover page:**
- Movie title, detected CEFR level, learner CEFR level, date
- Learner name field (blank line for handwriting)
- Score table showing Part A, B, C with point totals

**Part A: Vocabulary (Multiple Choice, 5 choices, ~15 questions)**
- (a) Vocabulary meaning in context — "What does [word] mean in this context?"
- (b) Fill-in-the-blank — "Complete the dialogue: ___"

**Part B: Comprehension (Multiple Choice, 5 choices, ~10 questions)**
- (c) Listening comprehension — "What did [character] mean when they said...?"
- (d) Grammar usage — "Which sentence uses the correct form?"

**Part C: Subjective Writing (~8 questions with handwriting boxes)**
- (e) Scene summarization
- (f) Character intent / emotion analysis
- (g) Alternative dialogue writing
- (h) Use vocabulary words in own sentences

**Total: ~33 questions per exercise** (adjustable based on movie length)

Question numbering follows: `A1 (2 points)`, `B3 (3 points)`, `C2 (10 points)`.

### 4.6 Guideline File

`<movie-name>-guideline.json` stores everything the assessment mode needs:

```json
{
  "movie": "<movie-name>",
  "detected_cefr": "B1",
  "learner_cefr": "A2",
  "generated_date": "2026-04-16",
  "parts": {
    "A": {
      "questions": [
        {
          "id": "A1",
          "type": "vocabulary_meaning",
          "prompt": "What does 'bow' mean in this context?",
          "choices": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."],
          "correct_answer": "C",
          "explanation": "In this scene, 'bow' refers to the front part of the ship..."
        }
      ]
    },
    "B": {
      "questions": [
        {
          "id": "B1",
          "type": "listening_comprehension",
          "prompt": "What did Jack mean when he said...?",
          "choices": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."],
          "correct_answer": "B",
          "explanation": "Jack was expressing..."
        }
      ]
    },
    "C": {
      "questions": [
        {
          "id": "C1",
          "type": "scene_summary",
          "prompt": "Summarize the scene where Jack and Rose meet at the bow.",
          "scene_ref": "scene_14",
          "scene_dialogue": [
            "Jack: Close your eyes. Do you trust me?",
            "Rose: I trust you."
          ],
          "rubric": {
            "max_score": 10,
            "criteria": {
              "content_accuracy": {
                "weight": 3,
                "description": "Correctly captures the key events of the scene",
                "key_points": [
                  "Jack asks Rose to close her eyes",
                  "Rose stands at the bow with arms spread",
                  "Moment of trust and freedom between them"
                ]
              },
              "grammar_and_structure": {
                "weight": 3,
                "description": "Uses correct grammar, sentence structure, and tenses",
                "expected_tenses": ["past simple", "past continuous"],
                "common_errors_to_check": ["subject-verb agreement", "tense consistency"]
              },
              "vocabulary_usage": {
                "weight": 2,
                "description": "Uses appropriate vocabulary from the movie or equivalent level",
                "target_words": ["trust", "bow", "flying", "ocean"]
              },
              "expression_and_depth": {
                "weight": 2,
                "description": "Shows understanding of emotion, context, or character motivation",
                "look_for": ["mentions trust theme", "describes emotional tone"]
              }
            }
          }
        },
        {
          "id": "C5",
          "type": "vocabulary_in_sentences",
          "prompt": "Use the words 'unsinkable', 'destiny', and 'courage' in your own sentences.",
          "rubric": {
            "max_score": 10,
            "criteria": {
              "correct_meaning": {
                "weight": 4,
                "description": "Each word is used with its correct meaning",
                "words": {
                  "unsinkable": "impossible to sink; cannot be defeated",
                  "destiny": "fate; predetermined course of events",
                  "courage": "bravery; ability to face fear"
                }
              },
              "grammar_and_structure": {
                "weight": 3,
                "description": "Sentences are grammatically correct and complete",
                "common_errors_to_check": ["sentence fragments", "word form errors"]
              },
              "context_appropriateness": {
                "weight": 3,
                "description": "Words are used in natural, meaningful contexts",
                "look_for": ["natural sentence flow", "logical context"]
              }
            }
          }
        }
      ]
    }
  },
  "vocabulary_list": [
    {
      "word": "bow",
      "part_of_speech": "noun",
      "cefr": "B1",
      "meaning": "front part of a ship",
      "movie_example": "\"I'm the king of the world!\" (at the bow)",
      "real_life_example": "The passengers gathered at the bow to watch the sunset.",
      "scene_ref": "scene_14"
    }
  ]
}
```

### 4.7 Vocabulary List PDF

**Structure:**
1. Cover page — Movie title, total word count, CEFR distribution summary
2. Table of Contents — grouped by CEFR level (A1 → C2)
3. Vocabulary tables per CEFR level, sorted alphabetically within each level:

| Word | Part of Speech | Meaning | Example from Movie | Real-life Example | Scene |
|------|---------------|---------|-------------------|-------------------|-------|
| bow | noun | front part of a ship | "I'm the king of the world!" (at the bow) | The passengers gathered at the bow to watch the sunset. | 14 |
| courage | noun | bravery; ability to face fear | "You have the courage to jump" | It takes courage to speak in front of a large audience. | 8 |

4. Summary — total words per CEFR level, most frequent words, recommended words to study first based on learner's level

---

## 5. Assess Mode

### 5.1 Assessment Flow

```
Scanned PDF (learner's completed exercise)
  → docling-mcp extracts content from PDF
  → Agent loads <movie-name>-guideline.json
  → Agent scores Part A & B (multiple choice) automatically
  → Agent evaluates Part C (subjective) using rubric criteria
  → Agent generates full learning report
  → render_latex.py fills assessment.tex.j2
  → compile_pdf.sh → <movie-name>-assessment.pdf
  → Also outputs <movie-name>-assessment.md
```

### 5.2 Assessment Report Structure (both MD and PDF)

1. **Cover page** — Movie title, learner level, assessment date, overall score

2. **Score Summary**
   - Part A: Vocabulary — score/total (e.g., 12/15)
   - Part B: Comprehension — score/total (e.g., 7/10)
   - Part C: Subjective Writing — score/total (e.g., 28/40)
   - Overall: 47/65 (72%)

3. **Part A & B: Detailed Results**
   - Each question: learner's answer, correct answer, status (checkmark/cross)
   - For incorrect answers: explanation of why the correct answer is right, referencing the movie scene

4. **Part C: Subjective Feedback**
   - Each question scored per rubric criteria (content, grammar, vocabulary, expression)
   - Specific inline corrections, e.g.:
     - "You wrote 'Jack tell Rose to close her eyes' — past tense: 'Jack **told** Rose to close her eyes'"
     - "Good use of the word 'trust' — your sentence captured the emotional tone of the scene"
   - Highlighted strong points and areas to improve

5. **Proficiency Assessment**
   - Current estimated CEFR level based on performance
   - Comparison with learner's self-declared level
   - Breakdown by skill: vocabulary strength, grammar accuracy, comprehension depth, writing expression

6. **Personalized Study Plan**
   - Weak areas — specific grammar rules, vocabulary gaps, or comprehension patterns
   - Recommended practice — e.g., "Practice past tense irregular verbs", "Study B1 phrasal verbs"
   - Suggested next movies — 3 movie recommendations matched to learner's current level and weak areas

---

## 6. LaTeX Formatting — CS188 Exam Style

All three PDFs share a common LaTeX style based on the UC Berkeley CS188 midterm exam format.

### 6.1 Shared Style (`common.tex.j2`)

- **Engine:** xelatex (Unicode support)
- **Font:** Computer Modern (default LaTeX font)
- **Page size:** A4
- **Color scheme:** Black and white, clean academic look
- **Header/Footer:** 3-column footer — "Exercise | Page X of Y | Movie — CEFR Level"
- **Continuation notes:** "(Part B continued...)" when content spans pages

### 6.2 Exercise PDF Formatting

- Circular bubbles for single-select multiple choice with labels A through E
- Answer boxes — bordered rectangular boxes with lines for handwriting (using `tcolorbox`)
- Question numbering: `A1 (2 points)`, `B3 (3 points)`, `C2 (10 points)`
- Score table on cover page
- Clear section breaks between Part A, B, C

### 6.3 Vocabulary PDF Formatting

- Simple bordered tables matching the exam's table style
- CEFR level as text label, e.g., `[B1]` before each word
- Same 3-column footer format
- Page break between each CEFR level section

### 6.4 Assessment PDF Formatting

- Checkmarks and crosses for correct/incorrect
- Score fractions like `(8/10)` next to section headers
- Feedback in bordered boxes (same style as exam answer boxes)
- Study plan as clean bullet lists
- Same 3-column footer format

---

## 7. Error Handling

| Scenario | Behavior |
|---|---|
| Unrecognized subtitle format | Clear error with supported formats (.srt, .vtt) |
| Scanned PDF unreadable | Report which questions could not be parsed, score only readable ones |
| Missing guideline.json | Tell learner to run generate first |
| xelatex not installed | Provide install instructions (e.g., `brew install --cask mactex`) |
| docling-mcp not configured | Provide setup instructions |
| Subtitle too short (<50 lines) | Warning that exercise quality may be limited, proceed anyway |

---

## 8. Decisions Summary

| Decision | Choice | Rationale |
|---|---|---|
| PDF generation | LaTeX (xelatex) | Professional typesetting, great for exercises with boxes/tables |
| Difficulty detection | Auto-detect + learner-specified | Combines movie analysis with personalization |
| Question types | All 8 (4 MC + 4 subjective) | Comprehensive skill coverage |
| Submission method | Scanned PDF only | Natural workflow — print, write, scan |
| Assessment depth | Full learning report | Maximum value for learner |
| Vocabulary tagging | CEFR (A1-C2) | International standard |
| Visual style | CS188 exam style | Clean, B&W, academic, professional |
| Skill structure | Single skill, two subcommands | One entry point for the user |
| Template engine | Jinja2 | Flexible, Python-native, clean syntax |
