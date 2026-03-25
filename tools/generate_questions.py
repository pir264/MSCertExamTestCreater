"""
Generates multiple-choice exam questions via the Claude API.
Returns a list of question dicts with objective, question, options, correct, explanation, reference.
"""

import json
import os
import random
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Official learning objectives per exam code
EXAM_OBJECTIVES: dict[str, list[str]] = {
    "DP-900": [
        "Describe core data concepts",
        "Identify considerations for relational data on Azure",
        "Describe considerations for working with non-relational data on Azure",
        "Describe an analytics workload on Azure",
    ],
    "AZ-900": [
        "Describe cloud concepts",
        "Describe Azure architecture and services",
        "Describe Azure management and governance",
    ],
    "AZ-104": [
        "Manage Azure identities and governance",
        "Implement and manage storage",
        "Deploy and manage Azure compute resources",
        "Implement and manage virtual networking",
        "Monitor and maintain Azure resources",
    ],
    "AZ-204": [
        "Develop Azure compute solutions",
        "Develop for Azure storage",
        "Implement Azure security",
        "Monitor, troubleshoot, and optimize Azure solutions",
        "Connect to and consume Azure services and third-party services",
    ],
    "AI-900": [
        "Describe Artificial Intelligence workloads and considerations",
        "Describe fundamental principles of machine learning on Azure",
        "Describe features of computer vision workloads on Azure",
        "Describe features of Natural Language Processing workloads on Azure",
        "Describe features of generative AI workloads on Azure",
    ],
    "SC-900": [
        "Describe security, compliance, and identity concepts",
        "Describe the capabilities of Microsoft Entra",
        "Describe the capabilities of Microsoft security solutions",
        "Describe the capabilities of Microsoft compliance solutions",
    ],
    "PL-900": [
        "Describe the business value of Microsoft Power Platform",
        "Identify the core components of Microsoft Power Platform",
        "Demonstrate the capabilities of Power BI",
        "Demonstrate the capabilities of Power Apps",
        "Demonstrate the capabilities of Power Automate",
        "Demonstrate the complementary Microsoft Power Platform solutions",
    ],
    "MS-900": [
        "Describe cloud concepts",
        "Describe Microsoft 365 apps and services",
        "Describe security, compliance, privacy, and trust in Microsoft 365",
        "Describe Microsoft 365 pricing and support",
    ],
}


def _build_prompt(
    exam_code: str,
    objectives: list[str],
    num_questions: int,
    weak_weights: dict[str, float],
) -> str:
    # Determine how many questions per objective based on weights
    if weak_weights:
        total_weight = sum(
            weak_weights.get(obj, 1.0) for obj in objectives
        )
        distribution = {
            obj: max(1, round(num_questions * weak_weights.get(obj, 1.0) / total_weight))
            for obj in objectives
        }
        # Adjust to exactly num_questions
        diff = num_questions - sum(distribution.values())
        if diff != 0:
            sorted_objs = sorted(
                objectives, key=lambda o: weak_weights.get(o, 1.0), reverse=True
            )
            for i in range(abs(diff)):
                if diff > 0:
                    distribution[sorted_objs[i % len(sorted_objs)]] += 1
                else:
                    if distribution[sorted_objs[i % len(sorted_objs)]] > 1:
                        distribution[sorted_objs[i % len(sorted_objs)]] -= 1
        distribution_text = "\n".join(
            f"- {obj}: {count} question(s)" for obj, count in distribution.items()
        )
    else:
        per_obj = max(1, num_questions // len(objectives))
        remainder = num_questions - per_obj * len(objectives)
        distribution_text = "\n".join(
            f"- {obj}: {per_obj + (1 if i < remainder else 0)} question(s)"
            for i, obj in enumerate(objectives)
        )

    weak_note = ""
    if weak_weights:
        weak_objs = sorted(
            weak_weights.items(), key=lambda x: x[1], reverse=True
        )[:3]
        if weak_objs:
            weak_note = (
                "\n\nIMPORTANT: The student has historically performed poorly on these objectives. "
                "Make sure to include questions that test these areas thoroughly:\n"
                + "\n".join(f"- {obj}" for obj, _ in weak_objs)
            )

    return f"""You are creating practice exam questions for the Microsoft {exam_code} certification exam.

Generate exactly {num_questions} multiple-choice questions distributed as follows:
{distribution_text}{weak_note}

Requirements for each question:
- 4 answer options labeled A, B, C, D
- Exactly 1 correct answer
- 3 plausible but clearly wrong distractors
- A concise explanation (2-4 sentences) of why the correct answer is right
- A reference URL from learn.microsoft.com relevant to the topic

Return ONLY a valid JSON array with no additional text. Each element must have exactly these fields:
{{
  "objective": "<one of the exam objectives listed above>",
  "question": "<the question text>",
  "options": {{
    "A": "<option A>",
    "B": "<option B>",
    "C": "<option C>",
    "D": "<option D>"
  }},
  "correct": "<A, B, C, or D>",
  "explanation": "<explanation of the correct answer>",
  "reference": "<https://learn.microsoft.com/... URL>"
}}

Make the questions realistic, exam-style, and varying in difficulty. Do not repeat questions."""


def generate_questions(
    exam_code: str,
    num_questions: int,
    weak_weights: dict[str, float] | None = None,
) -> list[dict]:
    """
    Generate num_questions multiple-choice questions for exam_code.
    weak_weights: optional {objective: weight} from progress_tracker.
    Returns list of question dicts.
    """
    exam_code = exam_code.upper()
    objectives = EXAM_OBJECTIVES.get(exam_code)
    if not objectives:
        raise ValueError(
            f"Exam '{exam_code}' is not in the known exams list. "
            f"Supported: {', '.join(EXAM_OBJECTIVES.keys())}"
        )

    if weak_weights is None:
        weak_weights = {}

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = _build_prompt(exam_code, objectives, num_questions, weak_weights)

    for attempt in range(2):
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            questions = json.loads(raw)
            _validate_questions(questions)
            return questions
        except (json.JSONDecodeError, ValueError) as e:
            if attempt == 0:
                continue
            raise RuntimeError(
                f"Failed to parse valid questions from Claude API after 2 attempts: {e}"
            ) from e

    return []


def _validate_questions(questions: list) -> None:
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Expected a non-empty JSON array of questions.")
    required_keys = {"objective", "question", "options", "correct", "explanation", "reference"}
    for i, q in enumerate(questions):
        missing = required_keys - set(q.keys())
        if missing:
            raise ValueError(f"Question {i} missing keys: {missing}")
        if not isinstance(q["options"], dict) or set(q["options"].keys()) != {"A", "B", "C", "D"}:
            raise ValueError(f"Question {i} options must have keys A, B, C, D.")
        if q["correct"] not in ("A", "B", "C", "D"):
            raise ValueError(f"Question {i} correct must be A, B, C, or D.")
