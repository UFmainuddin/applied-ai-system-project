"""Evaluation harness for the final PawPal+ system."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from pawpal_system import Owner, PawPalAssistant, Pet, Scheduler, Task


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass(frozen=True)
class EvaluationResult:
    """Store one evaluation outcome."""

    name: str
    passed: bool
    details: str


def build_owner_for_priority_scenario() -> Owner:
    owner = Owner("Jordan", 45)
    mochi = Pet("Mochi", "dog", 3)
    mochi.add_task(Task("Medication", "09:00", 20, due_date=date.today(), priority="high"))
    mochi.add_task(Task("Walk", "08:00", 30, due_date=date.today(), priority="low"))
    owner.add_pet(mochi)
    return owner


def build_owner_for_rag_scenario() -> Owner:
    owner = Owner("Jordan", 60)
    luna = Pet("Luna", "cat", 5)
    luna.add_task(Task("Medication", "08:00", 10, due_date=date.today(), priority="high"))
    owner.add_pet(luna)
    return owner


def evaluate_priority_planning() -> EvaluationResult:
    owner = build_owner_for_priority_scenario()
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())
    passed = len(plan) == 1 and plan[0].description == "Medication"
    return EvaluationResult(
        name="priority_planning",
        passed=passed,
        details=f"scheduled={[task.description for task in plan]}, skipped={[task.description for task in scheduler.skipped]}",
    )


def evaluate_rag_guidance() -> EvaluationResult:
    owner = build_owner_for_rag_scenario()
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())
    guidance = scheduler.task_guidance(plan[0]) if plan else []
    passed = bool(guidance) and "Medication" in guidance[0].source_title
    return EvaluationResult(
        name="rag_guidance",
        passed=passed,
        details=f"guidance_count={len(guidance)} first_source={(guidance[0].source_title if guidance else 'none')}",
    )


def evaluate_specialized_summary() -> EvaluationResult:
    owner = build_owner_for_rag_scenario()
    scheduler = Scheduler(owner)
    scheduler.generate_plan(date.today())
    assistant = PawPalAssistant(scheduler)
    baseline = assistant.baseline_summary(date.today())
    specialized = assistant.specialized_summary(date.today())
    passed = baseline != specialized and "PawPal Care Brief" in specialized
    return EvaluationResult(
        name="specialized_summary",
        passed=passed,
        details="baseline and specialized outputs are distinct",
    )


def evaluate_time_budget_guardrail() -> EvaluationResult:
    owner = build_owner_for_priority_scenario()
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())
    total_minutes = sum(task.duration_minutes for task in plan)
    passed = total_minutes <= owner.available_minutes
    return EvaluationResult(
        name="time_budget_guardrail",
        passed=passed,
        details=f"scheduled_minutes={total_minutes}, available_minutes={owner.available_minutes}",
    )


def main() -> None:
    results = [
        evaluate_priority_planning(),
        evaluate_rag_guidance(),
        evaluate_specialized_summary(),
        evaluate_time_budget_guardrail(),
    ]
    passed = sum(result.passed for result in results)

    print("PawPal+ Evaluation Summary")
    print("=========================")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} | {result.name} | {result.details}")
    print(f"Overall: {passed}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
