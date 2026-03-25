"""
Displays exam progress statistics as a rich table and a matplotlib line chart.
"""

import sys
from pathlib import Path

# Allow running as a standalone script
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.progress_tracker import load_progress


def show_stats(exam_code: str) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box
        _show_rich_table(exam_code)
    except ImportError:
        _show_plain_table(exam_code)

    _show_chart(exam_code)


def _show_rich_table(exam_code: str) -> None:
    from rich.console import Console
    from rich.table import Table
    from rich import box

    data = load_progress(exam_code)
    objectives = data.get("objectives", {})

    console = Console()
    console.print(f"\n[bold cyan]Statistics for {exam_code}[/bold cyan]\n")

    if not objectives:
        console.print("[yellow]No data yet. Complete a session first.[/yellow]")
        return

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Learning Objective", style="dim", no_wrap=False, max_width=50)
    table.add_column("Correct", justify="right")
    table.add_column("Incorrect", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("% Correct", justify="right")

    for obj, stats in objectives.items():
        correct = stats["total_correct"]
        incorrect = stats["total_incorrect"]
        total = correct + incorrect
        pct = (correct / total * 100) if total > 0 else 0.0
        color = "green" if pct >= 70 else ("yellow" if pct >= 50 else "red")
        table.add_row(
            obj,
            str(correct),
            str(incorrect),
            str(total),
            f"[{color}]{pct:.0f}%[/{color}]",
        )

    console.print(table)


def _show_plain_table(exam_code: str) -> None:
    data = load_progress(exam_code)
    objectives = data.get("objectives", {})

    print(f"\nStatistics for {exam_code}\n")
    print(f"{'Objective':<50} {'Correct':>8} {'Incorrect':>10} {'%':>8}")
    print("-" * 80)

    for obj, stats in objectives.items():
        correct = stats["total_correct"]
        incorrect = stats["total_incorrect"]
        total = correct + incorrect
        pct = (correct / total * 100) if total > 0 else 0.0
        print(f"{obj[:50]:<50} {correct:>8} {incorrect:>10} {pct:>7.0f}%")


def _show_chart(exam_code: str) -> None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime
    except ImportError:
        print("\nmatplotlib not installed — skipping chart.")
        return

    data = load_progress(exam_code)
    objectives = data.get("objectives", {})
    if not objectives:
        return

    # Build per-objective time series
    fig, ax = plt.subplots(figsize=(12, 6))
    has_data = False

    for obj, stats in objectives.items():
        sessions = stats.get("sessions", [])
        if len(sessions) < 1:
            continue

        dates = []
        pcts = []
        for s in sessions:
            total = s["correct"] + s["incorrect"]
            if total > 0:
                dates.append(datetime.fromisoformat(s["date"]))
                pcts.append(s["correct"] / total * 100)

        if dates:
            short_label = obj if len(obj) <= 35 else obj[:32] + "..."
            ax.plot(dates, pcts, marker="o", label=short_label)
            has_data = True

    if not has_data:
        plt.close(fig)
        return

    ax.set_title(f"{exam_code} — % Correct per Learning Objective over Time", fontsize=13)
    ax.set_xlabel("Date")
    ax.set_ylabel("% Correct")
    ax.set_ylim(0, 105)
    ax.axhline(70, color="green", linestyle="--", linewidth=0.8, label="70% threshold")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save and show
    output_path = Path(__file__).parent.parent / "data" / f"{exam_code}_progress.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=150)
    print(f"\nChart saved to {output_path}")
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python show_stats.py <EXAM_CODE>")
        sys.exit(1)
    show_stats(sys.argv[1])
