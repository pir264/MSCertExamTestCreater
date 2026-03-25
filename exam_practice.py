#!/usr/bin/env python3
"""
MS Certification Exam Practice Tool
Start with: python exam_practice.py
"""

import sys
from pathlib import Path

# Ensure tools/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from tools.progress_tracker import load_config, save_config, load_progress, save_progress, get_weak_objectives
from tools.generate_questions import generate_questions, EXAM_OBJECTIVES
from tools.show_stats import show_stats

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def print_header(text: str) -> None:
    if RICH:
        console.print(Panel(f"[bold cyan]{text}[/bold cyan]", box=box.DOUBLE))
    else:
        print(f"\n{'='*60}\n  {text}\n{'='*60}")


def print_info(text: str) -> None:
    if RICH:
        console.print(f"[dim]{text}[/dim]")
    else:
        print(text)


def print_success(text: str) -> None:
    if RICH:
        console.print(f"[bold green]{text}[/bold green]")
    else:
        print(text)


def print_error(text: str) -> None:
    if RICH:
        console.print(f"[bold red]{text}[/bold red]")
    else:
        print(text)


def ask(prompt: str, default: str = "") -> str:
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    try:
        answer = input(display).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return answer if answer else default


def ask_letter(prompt: str, valid: str = "ABCD") -> str:
    while True:
        answer = ask(prompt).upper()
        if answer in valid:
            return answer
        print_error(f"Please enter one of: {', '.join(valid)}")


# ── Quiz ─────────────────────────────────────────────────────────────────────

def run_quiz(questions: list[dict]) -> list[dict]:
    """Runs the interactive quiz. Returns results list."""
    results = []
    total = len(questions)

    for i, q in enumerate(questions, 1):
        if RICH:
            console.print(f"\n[bold]Question {i}/{total}[/bold]  "
                          f"[dim]({q['objective']})[/dim]")
            console.print(f"\n{q['question']}\n")
            for letter, text in q["options"].items():
                console.print(f"  [cyan]{letter}[/cyan]. {text}")
        else:
            print(f"\nQuestion {i}/{total}  ({q['objective']})")
            print(f"\n{q['question']}\n")
            for letter, text in q["options"].items():
                print(f"  {letter}. {text}")

        answer = ask_letter("\nYour answer")
        correct = answer == q["correct"]

        if correct:
            print_success("✓ Correct!")
        else:
            print_error(f"✗ Wrong. The correct answer was {q['correct']}.")

        results.append({
            "objective": q["objective"],
            "correct": correct,
            "question": q["question"],
            "user_answer": answer,
            "correct_answer": q["correct"],
            "options": q["options"],
            "explanation": q["explanation"],
            "reference": q["reference"],
        })

    return results


def show_feedback(results: list[dict]) -> None:
    """Shows explanation for each question after the quiz."""
    correct_count = sum(1 for r in results if r["correct"])
    total = len(results)

    print_header(f"Results: {correct_count}/{total} correct "
                 f"({correct_count/total*100:.0f}%)")

    for i, r in enumerate(results, 1):
        if RICH:
            status = "[green]✓ Correct[/green]" if r["correct"] else f"[red]✗ Wrong (you: {r['user_answer']}, answer: {r['correct_answer']})[/red]"
            console.print(f"\n[bold]Q{i}.[/bold] {r['question']}")
            console.print(f"    {status}")
            console.print(f"\n[dim]Explanation:[/dim] {r['explanation']}")
            console.print(f"[dim]Reference:[/dim] [link={r['reference']}]{r['reference']}[/link]")
        else:
            status = "✓ Correct" if r["correct"] else f"✗ Wrong (you: {r['user_answer']}, answer: {r['correct_answer']})"
            print(f"\nQ{i}. {r['question']}")
            print(f"  {status}")
            print(f"  Explanation: {r['explanation']}")
            print(f"  Reference: {r['reference']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print_header("Microsoft Certification Exam Practice")

    # 1. Load config and ask for exam/question count
    config = load_config()
    default_exam = config.get("default_exam", "")
    default_questions = config.get("default_questions", 10)

    known_exams = ", ".join(EXAM_OBJECTIVES.keys())
    print_info(f"Supported exams: {known_exams}")

    exam_code = ask("Exam code", default_exam).upper()
    if not exam_code:
        print_error("Exam code is required.")
        sys.exit(1)
    if exam_code not in EXAM_OBJECTIVES:
        print_error(f"Unknown exam '{exam_code}'. Supported: {known_exams}")
        sys.exit(1)

    num_str = ask("Number of questions", str(default_questions))
    try:
        num_questions = int(num_str)
        if num_questions < 1:
            raise ValueError
    except ValueError:
        print_error("Please enter a valid positive number.")
        sys.exit(1)

    # 2. Save new defaults
    save_config(exam_code, num_questions)

    # 3. Load weak objectives
    weak_weights = get_weak_objectives(exam_code)
    if weak_weights:
        weakest = sorted(weak_weights.items(), key=lambda x: x[1], reverse=True)[:2]
        print_info(f"Focusing extra attention on: {', '.join(o for o, _ in weakest)}")

    # 4. Generate questions
    print_info(f"\nGenerating {num_questions} questions for {exam_code}…")
    try:
        questions = generate_questions(exam_code, num_questions, weak_weights)
    except Exception as e:
        print_error(f"Failed to generate questions: {e}")
        sys.exit(1)

    print_success(f"Generated {len(questions)} questions.\n")

    # 5. Run quiz
    results = run_quiz(questions)

    # 6. Show feedback
    print()
    show_feedback_prompt = ask("\nShow full explanations? (y/n)", "y").lower()
    if show_feedback_prompt == "y":
        show_feedback(results)

    # 7. Save progress
    save_progress(exam_code, results)
    print_success("\nProgress saved.")

    # 8. Optionally show stats
    stats_prompt = ask("\nShow statistics? (y/n)", "y").lower()
    if stats_prompt == "y":
        show_stats(exam_code)


if __name__ == "__main__":
    main()
