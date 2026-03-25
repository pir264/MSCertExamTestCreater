"""
Reads and writes exam progress data to data/{EXAM}.json.
Tracks per-objective correct/incorrect counts and session history.
"""

import json
import os
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def _exam_file(exam_code: str) -> Path:
    return DATA_DIR / f"{exam_code.upper()}.json"


def load_progress(exam_code: str) -> dict:
    path = _exam_file(exam_code)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"exam_code": exam_code.upper(), "objectives": {}}


def save_progress(exam_code: str, session_results: list[dict]) -> None:
    """
    session_results: list of dicts with keys:
        objective (str), correct (bool)
    """
    DATA_DIR.mkdir(exist_ok=True)
    data = load_progress(exam_code)
    today = date.today().isoformat()

    # Aggregate session counts per objective
    session_counts: dict[str, dict] = {}
    for result in session_results:
        obj = result["objective"]
        if obj not in session_counts:
            session_counts[obj] = {"correct": 0, "incorrect": 0}
        if result["correct"]:
            session_counts[obj]["correct"] += 1
        else:
            session_counts[obj]["incorrect"] += 1

    for obj, counts in session_counts.items():
        if obj not in data["objectives"]:
            data["objectives"][obj] = {
                "total_correct": 0,
                "total_incorrect": 0,
                "sessions": [],
            }
        entry = data["objectives"][obj]
        entry["total_correct"] += counts["correct"]
        entry["total_incorrect"] += counts["incorrect"]
        entry["sessions"].append({
            "date": today,
            "correct": counts["correct"],
            "incorrect": counts["incorrect"],
        })

    with open(_exam_file(exam_code), "w") as f:
        json.dump(data, f, indent=2)


def get_weak_objectives(exam_code: str) -> dict[str, float]:
    """
    Returns a dict {objective: weight} where higher weight means weaker.
    Objectives with no history get weight 1.0 (neutral).
    Weight formula: 1 + (1 - pct_correct) so range is 1.0–2.0.
    """
    data = load_progress(exam_code)
    objectives = data.get("objectives", {})
    if not objectives:
        return {}

    weights = {}
    for obj, stats in objectives.items():
        total = stats["total_correct"] + stats["total_incorrect"]
        if total == 0:
            weights[obj] = 1.0
        else:
            pct_correct = stats["total_correct"] / total
            weights[obj] = round(1.0 + (1.0 - pct_correct), 4)
    return weights


def load_config() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    config_path = DATA_DIR / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {"default_exam": "", "default_questions": 10}


def save_config(exam_code: str, num_questions: int) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    config = {"default_exam": exam_code.upper(), "default_questions": num_questions}
    with open(DATA_DIR / "config.json", "w") as f:
        json.dump(config, f, indent=2)
