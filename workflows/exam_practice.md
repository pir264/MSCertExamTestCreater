# Workflow: MS Certification Exam Practice

## Objective
Generate adaptive multiple-choice practice questions for Microsoft Certification exams, track performance per learning objective, and visualize progress over time.

## Trigger
Run manually at any time:
```bash
python3 exam_practice.py
```

## Required Inputs
| Input | Source | Default |
|-------|--------|---------|
| Exam code (e.g. DP-900) | User prompt | Last used exam (`data/config.json`) |
| Number of questions | User prompt | Last used count (`data/config.json`) |
| ANTHROPIC_API_KEY | `.env` file | — |

## Supported Exams
DP-900, AZ-900, AZ-104, AZ-204, AI-900, SC-900, PL-900, MS-900

To add a new exam: add the exam code and its official learning objectives to `EXAM_OBJECTIVES` in `tools/generate_questions.py`.

## Tools Used
| Tool | Purpose |
|------|---------|
| `tools/generate_questions.py` | Calls Claude API to generate questions |
| `tools/progress_tracker.py` | Reads/writes `data/{EXAM}.json` and `data/config.json` |
| `tools/show_stats.py` | Renders a rich table + matplotlib line chart |

## Flow

```
1. Load defaults from data/config.json
2. Prompt: exam code + question count → save as new defaults
3. Load weak objectives from data/{EXAM}.json
4. Generate questions via Claude API (claude-sonnet-4-6)
   └─ Weak objectives get proportionally more questions
5. Interactive quiz: show question → user answers A/B/C/D → immediate correct/wrong
6. After all questions: show score + optional explanations with references
7. Save session results to data/{EXAM}.json
8. Optional: show statistics table + progress chart
```

## Data Files
```
data/
  config.json          # default_exam, default_questions
  {EXAM}.json          # per-objective totals + session history
  {EXAM}_progress.png  # chart (generated on demand, overwritten each time)
```

## Adaptive Question Logic
- Objectives with a lower historical % correct receive proportionally more questions.
- Weight formula: `1 + (1 − pct_correct)`, range 1.0–2.0.
- New exams (no history) distribute questions evenly across all objectives.

## Statistics
- **Table**: per objective — correct, incorrect, total, % correct (color-coded green/yellow/red).
- **Chart**: line graph of % correct per objective per session. Saved as `data/{EXAM}_progress.png`.

## Error Handling
- If the Claude API returns malformed JSON, it retries once automatically.
- If the exam code is unknown, the tool exits with a clear message.
- If `ANTHROPIC_API_KEY` is missing from `.env`, the Anthropic SDK raises an `AuthenticationError`.

## Setup (first time)
```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env and fill in your ANTHROPIC_API_KEY
```

## Starting the tool
```bash
# Activate the virtual environment first (every new terminal session)
source .venv/bin/activate

# Then run
python exam_practice.py
```

## Known Constraints
- Questions are generated fresh each session; they are not stored or reused.
- The chart requires a display (matplotlib GUI). On headless servers, the PNG is still saved.
- Only exams defined in `EXAM_OBJECTIVES` (generate_questions.py) are supported.
