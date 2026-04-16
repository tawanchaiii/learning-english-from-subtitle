# English Teacher Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code agent skill that generates English exercises from movie subtitles and assesses completed exercises, producing professional CS188-style PDFs.

**Architecture:** A single agent skill (`english-teacher.md`) orchestrates Python scripts for subtitle parsing and LaTeX rendering, Jinja2 templates for consistent PDF formatting, and docling-mcp for reading scanned PDFs. The skill has two modes: `generate` (subtitle to exercises) and `assess` (scanned PDF to learning report).

**Tech Stack:** Python 3, Jinja2, LaTeX (xelatex), tcolorbox, docling-mcp

**Spec:** `docs/superpowers/specs/2026-04-16-english-teacher-skill-design.md`

---

## File Structure

```
learning-english-from-subtitle/
├── .claude/
│   └── skills/
│       └── english-teacher.md              # Agent skill definition (both modes)
├── templates/
│   ├── common.tex.j2                       # Shared LaTeX preamble, fonts, header/footer
│   ├── exercise.tex.j2                     # Exercise PDF layout (bubbles, answer boxes)
│   ├── vocabulary.tex.j2                   # Vocabulary table layout (CEFR sections)
│   └── assessment.tex.j2                   # Assessment report layout (scores, feedback)
├── scripts/
│   ├── parse_subtitle.py                   # Parse .srt/.vtt to scenes JSON
│   ├── render_latex.py                     # Render Jinja2 template + JSON data to .tex
│   └── compile_pdf.sh                      # Compile .tex to .pdf via xelatex
├── tests/
│   ├── test_parse_subtitle.py              # Unit tests for subtitle parser
│   ├── test_render_latex.py                # Unit tests for template renderer
│   └── fixtures/
│       ├── sample.srt                      # Sample SRT subtitle for testing
│       ├── sample.vtt                      # Sample VTT subtitle for testing
│       └── Frozen-sample.srt               # Integration test fixture
├── output/                                 # Generated exercise folders (gitignored)
├── .gitignore
├── requirements.txt                        # Python dependencies
└── CLAUDE.md                               # Project instructions
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `CLAUDE.md`
- Create: `output/.gitkeep`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/.gitkeep`

- [ ] **Step 1: Create requirements.txt**

```
jinja2>=3.1
pytest>=8.0
```

- [ ] **Step 2: Create .gitignore**

```
output/*/
!output/.gitkeep
*.aux
*.log
*.out
*.toc
*.fls
*.fdb_latexmk
*.synctex.gz
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
venv/
.venv/
```

- [ ] **Step 3: Create CLAUDE.md**

```markdown
# Learning English from Subtitle

## Overview

Agent skill project that generates English exercises from movie subtitles and assesses completed exercises.

## Commands

- `/english-teacher generate <subtitle-file> --level <CEFR>` — Generate exercises from subtitle
- `/english-teacher assess <movie-folder> <scanned-pdf>` — Assess completed exercise

## Project Structure

- `scripts/` — Python scripts for parsing and rendering
- `templates/` — Jinja2 LaTeX templates
- `output/` — Generated exercise folders (gitignored)
- `tests/` — pytest test suite

## Development

\```bash
# Install dependencies
uv pip install -r requirements.txt --system

# Run tests
python3 -m pytest tests/ -v

# Compile a .tex file to PDF
bash scripts/compile_pdf.sh <file.tex>
\```

## Dependencies

- Python 3 with jinja2
- xelatex (TeX Live) for PDF generation
- docling-mcp for reading scanned PDFs (assess mode only)
```

- [ ] **Step 4: Create directory structure**

```bash
mkdir -p output templates scripts tests/fixtures
touch output/.gitkeep tests/__init__.py tests/fixtures/.gitkeep
```

- [ ] **Step 5: Install Python dependencies**

```bash
uv pip install -r requirements.txt --system
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore CLAUDE.md output/.gitkeep tests/__init__.py tests/fixtures/.gitkeep
git commit -m "chore: scaffold project structure with dependencies and CLAUDE.md"
```

---

### Task 2: Subtitle Parser — SRT Format

**Files:**
- Create: `scripts/parse_subtitle.py`
- Create: `tests/test_parse_subtitle.py`
- Create: `tests/fixtures/sample.srt`

- [ ] **Step 1: Create sample SRT fixture**

Create `tests/fixtures/sample.srt`:
```
1
00:00:01,000 --> 00:00:03,500
Jack, you're crazy!

2
00:00:04,000 --> 00:00:06,200
That's what everybody says, but with all due respect,

3
00:00:06,300 --> 00:00:08,800
I'm not the one hanging off the back of a ship.

4
00:00:20,000 --> 00:00:22,500
Come on, give me your hand.

5
00:00:22,800 --> 00:00:24,100
You don't want to do this.

6
00:00:30,000 --> 00:00:33,000
I'm the king of the world!

7
00:00:45,000 --> 00:00:47,500
Do you trust me?

8
00:00:47,800 --> 00:00:49,000
I trust you.
```

- [ ] **Step 2: Write failing tests for SRT parsing**

Create `tests/test_parse_subtitle.py`:
```python
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
    # sample.srt has gaps at ~12s (between line 3 and 4), ~6s (between 5 and 6),
    # ~12s (between 6 and 7)
    # So we expect 4 scenes:
    #   Scene 1: lines 1-3 (00:00:01 to 00:00:08)
    #   Scene 2: lines 4-5 (00:00:20 to 00:00:24)
    #   Scene 3: line 6 (00:00:30 to 00:00:33)
    #   Scene 4: lines 7-8 (00:00:45 to 00:00:49)
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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_parse_subtitle.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'parse_subtitle'`

- [ ] **Step 4: Implement SRT parser**

Create `scripts/parse_subtitle.py`:
```python
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
            line.strip() for line in lines[timestamp_line_idx + 1:] if line.strip()
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_parse_subtitle.py -v
```
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/parse_subtitle.py tests/test_parse_subtitle.py tests/fixtures/sample.srt
git commit -m "feat: add SRT subtitle parser with scene grouping"
```

---

### Task 3: Subtitle Parser — VTT Format

**Files:**
- Modify: `tests/test_parse_subtitle.py` (add VTT tests)
- Create: `tests/fixtures/sample.vtt`

- [ ] **Step 1: Create sample VTT fixture**

Create `tests/fixtures/sample.vtt`:
```
WEBVTT

00:00:01.000 --> 00:00:03.500
Jack, you're crazy!

00:00:04.000 --> 00:00:06.200
That's what everybody says, but with all due respect,

00:00:06.300 --> 00:00:08.800
I'm not the one hanging off the back of a ship.

00:00:20.000 --> 00:00:22.500
Come on, give me your hand.

00:00:22.800 --> 00:00:24.100
You don't want to do this.

00:00:30.000 --> 00:00:33.000
I'm the king of the world!

00:00:45.000 --> 00:00:47.500
Do you trust me?

00:00:47.800 --> 00:00:49.000
I trust you.
```

- [ ] **Step 2: Write failing tests for VTT parsing**

Add to `tests/test_parse_subtitle.py`:
```python
def test_parse_vtt_returns_dict_with_required_keys():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.vtt"))
    assert "filename" in result
    assert "movie_name" in result
    assert "format" in result
    assert "total_lines" in result
    assert "scenes" in result


def test_parse_vtt_extracts_movie_name():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.vtt"))
    assert result["movie_name"] == "sample"
    assert result["format"] == "vtt"


def test_parse_vtt_groups_scenes_same_as_srt():
    """VTT and SRT with same content should produce same scene grouping."""
    srt_result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.srt"))
    vtt_result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.vtt"))
    assert len(vtt_result["scenes"]) == len(srt_result["scenes"])
    assert vtt_result["total_lines"] == srt_result["total_lines"]


def test_parse_vtt_total_lines():
    result = parse_subtitle(os.path.join(FIXTURES_DIR, "sample.vtt"))
    assert result["total_lines"] == 8


def test_parse_unsupported_format_raises():
    import pytest
    with pytest.raises(ValueError, match="Unsupported subtitle format"):
        parse_subtitle("movie.txt")
```

- [ ] **Step 3: Run tests to verify all pass**

```bash
python3 -m pytest tests/test_parse_subtitle.py -v
```
Expected: All 11 tests PASS (VTT parser was already implemented in Task 2's parse_subtitle.py)

- [ ] **Step 4: Commit**

```bash
git add tests/test_parse_subtitle.py tests/fixtures/sample.vtt
git commit -m "test: add VTT parsing tests and fixture"
```

---

### Task 4: LaTeX Common Template

**Files:**
- Create: `templates/common.tex.j2`

- [ ] **Step 1: Create the shared LaTeX preamble template**

Create `templates/common.tex.j2`:
```latex
%% common.tex.j2 — Shared preamble for all English Teacher PDFs
%% Style: CS188 exam format (clean, black & white, academic)

\documentclass[a4paper,11pt]{article}

% Encoding and fonts
\usepackage{fontspec}
\usepackage{unicode-math}

% Page geometry
\usepackage[
  top=2.5cm,
  bottom=2.5cm,
  left=2.5cm,
  right=2.5cm
]{geometry}

% Headers and footers
\usepackage{fancyhdr}
\usepackage{lastpage}
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyfoot[L]{\small {{ doc_type }}}
\fancyfoot[C]{\small Page \thepage\ of \pageref{LastPage}}
\fancyfoot[R]{\small {{ movie_name }} --- {{ cefr_level }}}

% Typography
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{longtable}

% Boxes for answer areas
\usepackage[most]{tcolorbox}
\tcbset{
  answerbox/.style={
    colback=white,
    colframe=black,
    boxrule=0.5pt,
    arc=0pt,
    outer arc=0pt,
    left=4pt,
    right=4pt,
    top=4pt,
    bottom=4pt
  }
}

% Custom commands for bubble choices (single select — circular)
\usepackage{tikz}
\newcommand{\bubble}[1]{%
  \tikz[baseline=(char.base)]{%
    \node[shape=circle, draw, inner sep=1.5pt, minimum size=14pt] (char) {\textsf{#1}};%
  }%
}
% Filled bubble (for answer keys)
\newcommand{\filledbubble}[1]{%
  \tikz[baseline=(char.base)]{%
    \node[shape=circle, draw, fill=black, text=white, inner sep=1.5pt, minimum size=14pt] (char) {\textsf{#1}};%
  }%
}

% Checkmark and cross for assessment
\usepackage{amssymb}
\newcommand{\correct}{\checkmark}
\newcommand{\incorrect}{\texttimes}

% Score bar
\newcommand{\scorebar}[2]{%
  % #1 = score, #2 = total
  \begin{tikzpicture}[baseline=(current bounding box.center)]
    \fill[black!20] (0,0) rectangle (4,0.3);
    \pgfmathsetmacro{\fillwidth}{4*(#1/#2)}
    \fill[black!60] (0,0) rectangle (\fillwidth,0.3);
    \node[right] at (4.2,0.15) {\small #1/#2};
  \end{tikzpicture}%
}

% Section formatting
\usepackage{titlesec}
\titleformat{\section}{\large\bfseries}{}{0pt}{}[\vspace{-0.5em}\rule{\textwidth}{0.5pt}]
\titleformat{\subsection}{\normalsize\bfseries}{}{0pt}{}

% Lined writing area for subjective questions
\newcommand{\writingbox}[1]{%
  \begin{tcolorbox}[answerbox, height=#1]
    \foreach \i in {1,...,20}{%
      \vfill
      \noindent\rule{\linewidth}{0.2pt}%
    }
    \vfill
  \end{tcolorbox}%
}

% Question formatting
\newcommand{\question}[3]{%
  % #1 = question ID (e.g., A1)
  % #2 = points
  % #3 = question text
  \noindent\textbf{#1} (#2 points) #3%
  \vspace{0.5em}%
}

% Hyperref (load last)
\usepackage{hyperref}
\hypersetup{hidelinks}
```

- [ ] **Step 2: Verify template syntax is valid**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(
    loader=FileSystemLoader('templates'),
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='{{',
    variable_end_string='}}',
    comment_start_string='<#',
    comment_end_string='#>',
)
t = env.get_template('common.tex.j2')
print('Template parsed OK')
"
```
Expected: `Template parsed OK`

- [ ] **Step 3: Commit**

```bash
git add templates/common.tex.j2
git commit -m "feat: add shared LaTeX preamble template (CS188 exam style)"
```

---

### Task 5: Exercise LaTeX Template

**Files:**
- Create: `templates/exercise.tex.j2`

- [ ] **Step 1: Create the exercise template**

Create `templates/exercise.tex.j2`:
```latex
%% exercise.tex.j2 — Exercise PDF (CS188 exam style)

<% include 'common.tex.j2' %>

\begin{document}

%% ===== COVER PAGE =====
\thispagestyle{empty}

\noindent
\begin{minipage}[t]{0.5\textwidth}
\textbf{\Large English Exercise}\\[0.3em]
\textbf{\large {{ movie_name }}}
\end{minipage}%
\hfill
\begin{minipage}[t]{0.4\textwidth}
\raggedleft
Movie CEFR: {{ detected_cefr }}\\
Your Level: {{ learner_cefr }}\\
Date: {{ generated_date }}
\end{minipage}

\vspace{1.5em}

\noindent Print Your Name: \rule{8cm}{0.4pt}

\vspace{2em}

\noindent There are 3 parts of varying credit. ({{ total_points }} points total)

\vspace{1em}

\begin{center}
\begin{tabular}{|l|<% for part in parts %>c|<% endfor %>c|}
\hline
\textbf{Part} <% for part in parts %> & \textbf{ {{ part.label }} } <% endfor %> & \textbf{Total} \\
\hline
Points <% for part in parts %> & {{ part.points }} <% endfor %> & {{ total_points }} \\
\hline
\end{tabular}
\end{center}

\vspace{1.5em}

\noindent\textit{For questions with circular bubbles, you may select only one choice.}

\vspace{0.5em}
\begin{itemize}[leftmargin=2em]
  \item[\bubble{A}] Unselected option (completely unfilled)
  \item[\filledbubble{C}] Your selected option (completely filled)
\end{itemize}

\vspace{1em}

\noindent\textit{For subjective questions, write your answer clearly inside the answer box. Anything written outside the box will not be graded.}

\vspace{1em}
\noindent\rule{\textwidth}{0.5pt}

\newpage

%% ===== PART A: VOCABULARY (MULTIPLE CHOICE) =====
\section*{Part A: Vocabulary ({{ part_a_points }} points)}

<% for q in part_a_questions %>
\question{ {{ q.id }} }{ {{ q.points }} }{ {{ q.prompt }} }

\vspace{0.3em}
\begin{itemize}[leftmargin=2em, label={}]
<% for choice in q.choices %>
  \item[\bubble{ {{ choice.label }} }] {{ choice.text }}
<% endfor %>
\end{itemize}

\vspace{1em}
<% endfor %>

%% ===== PART B: COMPREHENSION (MULTIPLE CHOICE) =====
<% if part_b_needs_newpage %>\newpage<% endif %>
\section*{Part B: Comprehension ({{ part_b_points }} points)}

<% for q in part_b_questions %>
\question{ {{ q.id }} }{ {{ q.points }} }{ {{ q.prompt }} }

\vspace{0.3em}
\begin{itemize}[leftmargin=2em, label={}]
<% for choice in q.choices %>
  \item[\bubble{ {{ choice.label }} }] {{ choice.text }}
<% endfor %>
\end{itemize}

\vspace{1em}
<% endfor %>

%% ===== PART C: SUBJECTIVE WRITING =====
\newpage
\section*{Part C: Subjective Writing ({{ part_c_points }} points)}

<% for q in part_c_questions %>
\question{ {{ q.id }} }{ {{ q.points }} }{ {{ q.prompt }} }

\vspace{0.5em}
\writingbox{ {{ q.box_height }} }

<% if not loop.last %>
\vspace{1.5em}
<% endif %>

<% if q.needs_newpage %>\newpage<% endif %>
<% endfor %>

\end{document}
```

- [ ] **Step 2: Verify template parses**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(
    loader=FileSystemLoader('templates'),
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='{{',
    variable_end_string='}}',
    comment_start_string='<#',
    comment_end_string='#>',
)
t = env.get_template('exercise.tex.j2')
print('Exercise template parsed OK')
"
```
Expected: `Exercise template parsed OK`

- [ ] **Step 3: Commit**

```bash
git add templates/exercise.tex.j2
git commit -m "feat: add exercise LaTeX template with MC bubbles and writing boxes"
```

---

### Task 6: Vocabulary LaTeX Template

**Files:**
- Create: `templates/vocabulary.tex.j2`

- [ ] **Step 1: Create the vocabulary template**

Create `templates/vocabulary.tex.j2`:
```latex
%% vocabulary.tex.j2 — Vocabulary List PDF (CS188 exam style)

<% include 'common.tex.j2' %>

\begin{document}

%% ===== COVER PAGE =====
\thispagestyle{empty}

\noindent
\begin{minipage}[t]{0.5\textwidth}
\textbf{\Large Vocabulary List}\\[0.3em]
\textbf{\large {{ movie_name }}}
\end{minipage}%
\hfill
\begin{minipage}[t]{0.4\textwidth}
\raggedleft
Movie CEFR: {{ detected_cefr }}\\
Total Words: {{ total_words }}\\
Date: {{ generated_date }}
\end{minipage}

\vspace{2em}

\section*{CEFR Distribution}

\begin{center}
\begin{tabular}{|l|c|}
\hline
\textbf{Level} & \textbf{Count} \\
\hline
<% for level in cefr_levels %>
{{ level.name }} & {{ level.count }} \\
\hline
<% endfor %>
\end{tabular}
\end{center}

\vspace{1em}

\section*{Recommended Study Order}

\noindent Based on your level ({{ learner_cefr }}), focus on these words first:
\begin{enumerate}[leftmargin=2em]
<% for word in priority_words %>
  \item \textbf{ {{ word }} }
<% endfor %>
\end{enumerate}

\newpage

%% ===== VOCABULARY TABLES BY CEFR LEVEL =====
<% for level in cefr_sections %>
\section*{[{{ level.name }}] --- {{ level.description }}}

\noindent {{ level.count }} words

\vspace{0.5em}

\begin{longtable}{p{2.2cm} p{1.5cm} p{3cm} p{3.5cm} p{3.5cm}}
\toprule
\textbf{Word} & \textbf{POS} & \textbf{Meaning} & \textbf{Movie Example} & \textbf{Real-life Example} \\
\midrule
\endhead
\bottomrule
\endfoot
<% for word in level.words %>
{{ word.word }} & {{ word.pos }} & {{ word.meaning }} & \textit{ {{ word.movie_example }} } & {{ word.real_life_example }} \\
\midrule
<% endfor %>
\end{longtable}

<% if not loop.last %>\newpage<% endif %>
<% endfor %>

\end{document}
```

- [ ] **Step 2: Verify template parses**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(
    loader=FileSystemLoader('templates'),
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='{{',
    variable_end_string='}}',
    comment_start_string='<#',
    comment_end_string='#>',
)
t = env.get_template('vocabulary.tex.j2')
print('Vocabulary template parsed OK')
"
```
Expected: `Vocabulary template parsed OK`

- [ ] **Step 3: Commit**

```bash
git add templates/vocabulary.tex.j2
git commit -m "feat: add vocabulary list LaTeX template with CEFR sections"
```

---

### Task 7: Assessment LaTeX Template

**Files:**
- Create: `templates/assessment.tex.j2`

- [ ] **Step 1: Create the assessment template**

Create `templates/assessment.tex.j2`:
```latex
%% assessment.tex.j2 — Assessment Report PDF (CS188 exam style)

<% include 'common.tex.j2' %>

\begin{document}

%% ===== COVER PAGE =====
\thispagestyle{empty}

\noindent
\begin{minipage}[t]{0.5\textwidth}
\textbf{\Large Assessment Report}\\[0.3em]
\textbf{\large {{ movie_name }}}
\end{minipage}%
\hfill
\begin{minipage}[t]{0.4\textwidth}
\raggedleft
Learner Level: {{ learner_cefr }}\\
Assessment Date: {{ assessment_date }}\\
Overall Score: \textbf{ {{ overall_score }}/{{ overall_total }} ({{ overall_percent }}\%)}
\end{minipage}

\vspace{2em}

\section*{Score Summary}

\begin{center}
\begin{tabular}{|l|c|c|}
\hline
\textbf{Part} & \textbf{Score} & \textbf{Visual} \\
\hline
<% for part in score_parts %>
{{ part.label }} & {{ part.score }}/{{ part.total }} & \scorebar{ {{ part.score }} }{ {{ part.total }} } \\
\hline
<% endfor %>
\textbf{Overall} & \textbf{ {{ overall_score }}/{{ overall_total }} } & \scorebar{ {{ overall_score }} }{ {{ overall_total }} } \\
\hline
\end{tabular}
\end{center}

\newpage

%% ===== PART A & B: DETAILED RESULTS =====
\section*{Part A: Vocabulary --- Detailed Results ({{ part_a_score }}/{{ part_a_total }})}

<% for q in part_a_results %>
\noindent\textbf{ {{ q.id }} } {{ q.prompt }}\\
Your answer: \textbf{ {{ q.learner_answer }} } \hfill
Correct answer: \textbf{ {{ q.correct_answer }} } \hfill
<% if q.is_correct %>$\checkmark$ Correct<% else %>$\times$ Incorrect<% endif %>

<% if not q.is_correct %>
\begin{tcolorbox}[answerbox]
\textit{ {{ q.explanation }} }
\end{tcolorbox}
\vspace{0.3em}
<% endif %>

<% endfor %>

\section*{Part B: Comprehension --- Detailed Results ({{ part_b_score }}/{{ part_b_total }})}

<% for q in part_b_results %>
\noindent\textbf{ {{ q.id }} } {{ q.prompt }}\\
Your answer: \textbf{ {{ q.learner_answer }} } \hfill
Correct answer: \textbf{ {{ q.correct_answer }} } \hfill
<% if q.is_correct %>$\checkmark$ Correct<% else %>$\times$ Incorrect<% endif %>

<% if not q.is_correct %>
\begin{tcolorbox}[answerbox]
\textit{ {{ q.explanation }} }
\end{tcolorbox}
\vspace{0.3em}
<% endif %>

<% endfor %>

%% ===== PART C: SUBJECTIVE FEEDBACK =====
\newpage
\section*{Part C: Subjective Writing --- Detailed Feedback ({{ part_c_score }}/{{ part_c_total }})}

<% for q in part_c_results %>
\subsection*{ {{ q.id }} ({{ q.score }}/{{ q.max_score }}): {{ q.prompt }} }

\noindent\textbf{Your answer:}
\begin{tcolorbox}[answerbox]
{{ q.learner_answer }}
\end{tcolorbox}

\vspace{0.5em}

\noindent\textbf{Criteria scores:}
\begin{itemize}[leftmargin=2em]
<% for criterion in q.criteria_scores %>
  \item \textbf{ {{ criterion.name }} } ({{ criterion.score }}/{{ criterion.max }}): {{ criterion.feedback }}
<% endfor %>
\end{itemize}

<% if q.corrections %>
\noindent\textbf{Corrections:}
\begin{itemize}[leftmargin=2em]
<% for correction in q.corrections %>
  \item {{ correction }}
<% endfor %>
\end{itemize}
<% endif %>

<% if q.strengths %>
\noindent\textbf{Strengths:}
\begin{itemize}[leftmargin=2em]
<% for strength in q.strengths %>
  \item {{ strength }}
<% endfor %>
\end{itemize>
<% endif %>

\vspace{1em}
<% endfor %>

%% ===== PROFICIENCY ASSESSMENT =====
\newpage
\section*{Proficiency Assessment}

\noindent\textbf{Estimated CEFR Level:} {{ estimated_cefr }}\\
\textbf{Self-declared Level:} {{ learner_cefr }}\\
\textbf{Comparison:} {{ cefr_comparison }}

\vspace{1em}

\noindent\textbf{Skill Breakdown:}

\begin{center}
\begin{tabular}{|l|c|l|}
\hline
\textbf{Skill} & \textbf{Level} & \textbf{Assessment} \\
\hline
<% for skill in skill_breakdown %>
{{ skill.name }} & {{ skill.level }} & {{ skill.assessment }} \\
\hline
<% endfor %>
\end{tabular}
\end{center}

%% ===== PERSONALIZED STUDY PLAN =====
\vspace{1.5em}
\section*{Personalized Study Plan}

\subsection*{Weak Areas to Focus On}
\begin{itemize}[leftmargin=2em]
<% for area in weak_areas %>
  \item \textbf{ {{ area.topic }} }: {{ area.detail }}
<% endfor %>
\end{itemize}

\subsection*{Recommended Practice}
\begin{itemize}[leftmargin=2em]
<% for rec in recommendations %>
  \item {{ rec }}
<% endfor %>
\end{itemize}

\subsection*{Suggested Next Movies}
\begin{enumerate}[leftmargin=2em]
<% for movie in suggested_movies %>
  \item \textbf{ {{ movie.title }} } ({{ movie.cefr }}) --- {{ movie.reason }}
<% endfor %>
\end{enumerate}

\end{document}
```

- [ ] **Step 2: Verify template parses**

```bash
python3 -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(
    loader=FileSystemLoader('templates'),
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='{{',
    variable_end_string='}}',
    comment_start_string='<#',
    comment_end_string='#>',
)
t = env.get_template('assessment.tex.j2')
print('Assessment template parsed OK')
"
```
Expected: `Assessment template parsed OK`

- [ ] **Step 3: Commit**

```bash
git add templates/assessment.tex.j2
git commit -m "feat: add assessment report LaTeX template with scores and feedback"
```

---

### Task 8: LaTeX Render Script

**Files:**
- Create: `scripts/render_latex.py`
- Create: `tests/test_render_latex.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_render_latex.py`:
```python
import json
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_render_latex.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'render_latex'`

- [ ] **Step 3: Implement render script**

Create `scripts/render_latex.py`:
```python
"""Render Jinja2 LaTeX templates with data to produce .tex files."""

import json
import os
import sys

from jinja2 import Environment, FileSystemLoader


def render_template(
    template_name: str,
    data: dict,
    output_path: str,
    templates_dir: str = None,
) -> str:
    """Render a Jinja2 LaTeX template with data and write to output_path.

    Uses <% %> for blocks and {{ }} for variables to avoid conflicts
    with LaTeX curly braces in most contexts.

    Args:
        template_name: Name of the template file (e.g., 'exercise.tex.j2').
        data: Dict of template variables.
        output_path: Path to write the rendered .tex file.
        templates_dir: Path to templates directory. Defaults to ../templates/.

    Returns:
        The output_path where the file was written.
    """
    if templates_dir is None:
        templates_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "templates"
        )

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="{{",
        variable_end_string="}}",
        comment_start_string="<#",
        comment_end_string="#>",
    )

    template = env.get_template(template_name)
    rendered = template.render(**data)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python render_latex.py <template> <data.json> <output.tex>")
        sys.exit(1)

    template_name = sys.argv[1]
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        data = json.load(f)
    output_path = sys.argv[3]

    render_template(template_name, data, output_path)
    print(f"Rendered to {output_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_render_latex.py -v
```
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/render_latex.py tests/test_render_latex.py
git commit -m "feat: add Jinja2 LaTeX template renderer"
```

---

### Task 9: PDF Compile Script

**Files:**
- Create: `scripts/compile_pdf.sh`

- [ ] **Step 1: Create the compile script**

Create `scripts/compile_pdf.sh`:
```bash
#!/usr/bin/env bash
# compile_pdf.sh — Compile .tex files to PDF using xelatex
# Usage: bash scripts/compile_pdf.sh <file.tex> [output-dir]
#
# Runs xelatex twice (for cross-references like page numbers),
# then cleans up auxiliary files.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: bash scripts/compile_pdf.sh <file.tex> [output-dir]"
    exit 1
fi

TEX_FILE="$1"
OUTPUT_DIR="${2:-$(dirname "$TEX_FILE")}"

if [ ! -f "$TEX_FILE" ]; then
    echo "Error: File not found: $TEX_FILE"
    exit 1
fi

if ! command -v xelatex &> /dev/null; then
    echo "Error: xelatex not found. Install TeX Live:"
    echo "  macOS:  brew install --cask mactex"
    echo "  Ubuntu: sudo apt-get install texlive-xetex texlive-fonts-recommended"
    exit 1
fi

BASENAME=$(basename "$TEX_FILE" .tex)

echo "Compiling $TEX_FILE to $OUTPUT_DIR/$BASENAME.pdf"

# Run xelatex twice for cross-references (page numbers, TOC)
xelatex -interaction=nonstopmode -output-directory="$OUTPUT_DIR" "$TEX_FILE" > /dev/null 2>&1
xelatex -interaction=nonstopmode -output-directory="$OUTPUT_DIR" "$TEX_FILE" > /dev/null 2>&1

# Clean up auxiliary files
for ext in aux log out toc fls fdb_latexmk synctex.gz; do
    rm -f "$OUTPUT_DIR/$BASENAME.$ext"
done

if [ -f "$OUTPUT_DIR/$BASENAME.pdf" ]; then
    echo "Success: $OUTPUT_DIR/$BASENAME.pdf"
else
    echo "Error: PDF was not generated"
    exit 1
fi
```

- [ ] **Step 2: Make executable and verify**

```bash
chmod +x scripts/compile_pdf.sh
bash scripts/compile_pdf.sh 2>&1 || true
```
Expected: Shows usage message

- [ ] **Step 3: Commit**

```bash
git add scripts/compile_pdf.sh
git commit -m "feat: add xelatex PDF compilation script"
```

---

### Task 10: Agent Skill Definition

**Files:**
- Create: `.claude/skills/english-teacher.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p .claude/skills
```

- [ ] **Step 2: Create the agent skill file**

Create `.claude/skills/english-teacher.md` with the full skill definition covering both generate and assess modes. The complete content is specified in the design spec Section 1.

The skill file must include:
- Frontmatter with name, description, and argument-hint
- Mode detection logic (generate vs assess)
- Generate mode: 8 steps from subtitle parsing through PDF generation
- Assess mode: 8 steps from PDF extraction through report generation
- LaTeX style notes referencing the CS188 format
- Prerequisites checks for xelatex, jinja2, and docling-mcp

The full content of this file is provided in the design spec and is too large to inline here. Refer to the spec section "Task 10: Agent Skill Definition" for the complete markdown content.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/english-teacher.md
git commit -m "feat: add english-teacher agent skill definition (generate + assess modes)"
```

---

### Task 11: End-to-End Integration Test — Generate Mode

**Files:**
- Create: `tests/fixtures/Frozen-sample.srt`

- [ ] **Step 1: Create a small but realistic sample subtitle**

Create `tests/fixtures/Frozen-sample.srt`:
```
1
00:01:15,000 --> 00:01:18,500
Elsa? Do you want to build a snowman?

2
00:01:19,000 --> 00:01:21,200
Come on, let's go and play!

3
00:01:21,500 --> 00:01:24,800
I never see you anymore. Come out the door.

4
00:01:25,000 --> 00:01:27,500
It's like you've gone away.

5
00:02:00,000 --> 00:02:03,500
The cold never bothered me anyway.

6
00:02:04,000 --> 00:02:07,200
Let it go, let it go. Can't hold it back anymore.

7
00:02:07,500 --> 00:02:10,800
Let it go, let it go. Turn away and slam the door.

8
00:03:30,000 --> 00:03:33,000
Some people are worth melting for.

9
00:03:34,000 --> 00:03:37,500
Olaf, you're melting!

10
00:03:38,000 --> 00:03:40,200
I know. But some things are worth it.

11
00:05:00,000 --> 00:05:03,500
I'm not leaving here without you, Elsa.

12
00:05:04,000 --> 00:05:07,000
Yes, you are. I belong here. Alone.

13
00:05:07,500 --> 00:05:10,800
Where I can be who I am without hurting anybody.

14
00:05:20,000 --> 00:05:23,500
Love is an open door.

15
00:05:24,000 --> 00:05:27,200
With you, with you, with you, with you.
```

- [ ] **Step 2: Run the subtitle parser on the fixture**

```bash
python3 scripts/parse_subtitle.py tests/fixtures/Frozen-sample.srt
```
Expected: JSON output with scenes grouped by time gaps

- [ ] **Step 3: Test the render pipeline with minimal exercise data**

```bash
mkdir -p output/Frozen-sample
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from render_latex import render_template

data = {
    'doc_type': 'Exercise',
    'movie_name': 'Frozen-sample',
    'cefr_level': 'A2',
    'detected_cefr': 'A2',
    'learner_cefr': 'A1',
    'generated_date': '2026-04-16',
    'total_points': 10,
    'parts': [{'label': 'A', 'points': 4}, {'label': 'B', 'points': 3}, {'label': 'C', 'points': 3}],
    'part_a_points': 4,
    'part_a_questions': [{
        'id': 'A1', 'points': 2,
        'prompt': 'What does snowman mean in this context?',
        'choices': [
            {'label': 'A', 'text': 'A type of winter sport'},
            {'label': 'B', 'text': 'A figure made of snow'},
            {'label': 'C', 'text': 'A cold person'},
            {'label': 'D', 'text': 'A winter storm'},
            {'label': 'E', 'text': 'A frozen lake'},
        ]
    }],
    'part_b_points': 3,
    'part_b_questions': [],
    'part_b_needs_newpage': True,
    'part_c_points': 3,
    'part_c_questions': [{
        'id': 'C1', 'points': 3,
        'prompt': 'Summarize what happens between Anna and Elsa.',
        'box_height': '6cm',
        'needs_newpage': False,
    }],
}

render_template('exercise.tex.j2', data, 'output/Frozen-sample/Frozen-sample-exercise.tex')
print('Render OK')
"
```
Expected: `Render OK`

- [ ] **Step 4: Compile the .tex to PDF**

```bash
bash scripts/compile_pdf.sh output/Frozen-sample/Frozen-sample-exercise.tex
```
Expected: `Success: output/Frozen-sample/Frozen-sample-exercise.pdf`

- [ ] **Step 5: Verify the PDF exists and is non-empty**

```bash
ls -la output/Frozen-sample/Frozen-sample-exercise.pdf
```
Expected: File exists, size > 0

- [ ] **Step 6: Clean up test output and commit fixture**

```bash
rm -rf output/Frozen-sample
git add tests/fixtures/Frozen-sample.srt
git commit -m "test: add end-to-end integration test fixture for generate mode"
```

---

### Task 12: docling-mcp Configuration

**Files:**
- Modify: `.claude/settings.local.json`

- [ ] **Step 1: Read current settings**

Read `.claude/settings.local.json` to see existing configuration.

- [ ] **Step 2: Add docling-mcp to MCP server configuration**

Update `.claude/settings.local.json` to include:
```json
{
  "permissions": {
    "allow": [
      "Bash(rtk ls *)",
      "Bash(python3 scripts/*)",
      "Bash(bash scripts/compile_pdf.sh *)"
    ]
  },
  "mcpServers": {
    "docling-mcp": {
      "command": "uvx",
      "args": ["--from", "docling-mcp", "docling-mcp-server", "--transport", "stdio"]
    }
  }
}
```

- [ ] **Step 3: Verify docling-mcp installs and starts**

```bash
uvx --from docling-mcp docling-mcp-server --help 2>&1 | head -5
```
Expected: Help output or version info confirming the package exists

- [ ] **Step 4: Commit**

```bash
git add .claude/settings.local.json
git commit -m "chore: configure docling-mcp server for PDF reading in assess mode"
```

---

## Task Dependencies

```
Task 1 (scaffolding)
  ├── Task 2 (SRT parser) → Task 3 (VTT parser)
  ├── Task 4 (common template) → Task 5 (exercise template)
  │                            → Task 6 (vocabulary template)
  │                            → Task 7 (assessment template)
  ├── Task 8 (render script)
  └── Task 9 (compile script)
      └── All above → Task 10 (skill definition)
                    → Task 11 (integration test)
                    → Task 12 (docling-mcp config)
```

**Parallel opportunities:**
- After Task 1: Tasks 2, 4, 8, 9 can run in parallel
- After Task 4: Tasks 5, 6, 7 can run in parallel
- After Task 2: Task 3 can start
- Tasks 10, 11, 12 depend on all prior tasks
