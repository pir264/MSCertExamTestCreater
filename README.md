# MS Cert Exam Practice

An adaptive CLI study tool for Microsoft Certification exams. It generates fresh multiple-choice questions each session using the Claude AI API, tracks your performance per learning objective, and focuses on your weak areas over time.

## Features

- **Adaptive questioning** — weak learning objectives get more questions in the next session
- **8 supported exams** — DP-900, AZ-900, AZ-104, AZ-204, AI-900, SC-900, PL-900, MS-900
- **Instant feedback** — explanation and Microsoft Learn reference link after every question
- **Progress tracking** — per-objective history stored locally in JSON
- **Statistics** — rich terminal table + line chart showing % correct per objective over time
- **Remembers your defaults** — last used exam code and question count are saved automatically

## Demo

```
╔══════════════════════════════════════════════════════════════╗
║         Microsoft Certification Exam Practice                ║
╚══════════════════════════════════════════════════════════════╝

Supported exams: DP-900, AZ-900, AZ-104, AZ-204, AI-900, SC-900, PL-900, MS-900
Exam code [DP-900]:
Number of questions [10]:

Focusing extra attention on: Describe core data concepts, Describe an analytics workload on Azure

Generating 10 questions for DP-900…

Question 1/10  (Describe core data concepts)

Which of the following best describes a data lakehouse?

  A. A relational database optimized for OLTP workloads
  B. A storage architecture combining the flexibility of a data lake with the structure of a data warehouse
  C. A NoSQL document store for unstructured data
  D. A streaming platform for real-time event processing

Your answer: B
✓ Correct!
```

## Requirements

| Requirement | Details |
|---|---|
| Python | 3.10 or higher |
| Anthropic API key | Required for question generation — [get one here](https://console.anthropic.com) |
| Internet connection | Needed for each session (API calls to Claude) |

### Python packages

| Package | Purpose |
|---|---|
| `anthropic` | Calls the Claude API to generate questions |
| `rich` | Formatted terminal output (tables, colors) |
| `matplotlib` | Progress charts |
| `python-dotenv` | Loads `ANTHROPIC_API_KEY` from `.env` |

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/pir264/MSCertExamTestCreater.git
cd MSCertExamTestCreater
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

You can get a key at [console.anthropic.com](https://console.anthropic.com) → **API Keys** → **Create Key**.

## Usage

Activate the virtual environment, then run:

```bash
source .venv/bin/activate
python exam_practice.py
```

You will be prompted for:
- **Exam code** (e.g. `DP-900`) — defaults to the last exam you used
- **Number of questions** (e.g. `10`) — defaults to the last count you used

Answer each question by typing `A`, `B`, `C`, or `D`. After all questions you can view explanations and a statistics report.

### Viewing statistics only

```bash
python tools/show_stats.py DP-900
```

This shows the progress table and chart without starting a new quiz session.

## Supported Exams

| Code | Exam |
|------|------|
| DP-900 | Microsoft Azure Data Fundamentals |
| AZ-900 | Microsoft Azure Fundamentals |
| AZ-104 | Microsoft Azure Administrator |
| AZ-204 | Developing Solutions for Microsoft Azure |
| AI-900 | Microsoft Azure AI Fundamentals |
| SC-900 | Microsoft Security, Compliance, and Identity Fundamentals |
| PL-900 | Microsoft Power Platform Fundamentals |
| MS-900 | Microsoft 365 Fundamentals |

### Adding a new exam

Open [tools/generate_questions.py](tools/generate_questions.py) and add an entry to the `EXAM_OBJECTIVES` dictionary:

```python
"XX-000": [
    "Learning objective 1",
    "Learning objective 2",
],
```

## Data & Privacy

All progress data is stored **locally** in the `data/` directory (gitignored). Nothing is sent anywhere except the question generation prompt to the Anthropic API.

```
data/
  config.json        # your default exam and question count
  DP-900.json        # per-objective history for DP-900
  DP-900_progress.png
```

## Estimated API Cost

Question generation uses `claude-sonnet-4-6`. Approximate costs:

| Session | Tokens (in/out) | Estimated cost |
|---------|-----------------|----------------|
| 10 questions | ~700 / ~3,500 | ~$0.05 |
| 100 questions (10 sessions) | ~7,000 / ~35,000 | ~$0.50 |

Costs are dominated by output tokens (each question includes an explanation and reference). Check current pricing at [anthropic.com/pricing](https://www.anthropic.com/pricing).

## Project Structure

```
exam_practice.py          # entry point
tools/
  generate_questions.py   # Claude API call + question validation
  progress_tracker.py     # read/write data/*.json
  show_stats.py           # terminal table + matplotlib chart
workflows/
  exam_practice.md        # WAT-framework SOP
data/                     # created at runtime, gitignored
requirements.txt
.env.example
```

## License

MIT
