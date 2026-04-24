"""Core classes and scheduling logic for the PawPal+ app."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}
DEFAULT_KNOWLEDGE_BASE_PATH = Path(__file__).with_name("knowledge_base.json")
TASK_TYPE_KEYWORDS = {
    "medication": ["med", "medication", "medicine", "pill", "liquid", "dose"],
    "feeding": ["food", "feed", "breakfast", "dinner", "meal", "eat"],
    "walk": ["walk", "outdoor", "potty", "exercise"],
    "play": ["play", "toy", "window", "enrichment", "fetch"],
    "grooming": ["groom", "brush", "bath", "coat", "nail"],
    "vet": ["vet", "veterinarian", "checkup", "appointment", "clinic"],
    "hygiene": ["litter", "clean", "box", "hygiene"],
}


def _time_sort_key(value: str) -> tuple[int, int]:
    """Convert HH:MM text into a sortable tuple."""
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour, parsed.minute


def _minutes_from_time(value: str) -> int:
    """Convert HH:MM text into total minutes."""
    hour, minute = _time_sort_key(value)
    return hour * 60 + minute


def _time_from_minutes(value: int) -> str:
    """Convert total minutes back into HH:MM text."""
    hour = value // 60
    minute = value % 60
    return f"{hour:02d}:{minute:02d}"


def _normalize_words(value: str) -> set[str]:
    """Lowercase and split free text into word tokens."""
    return set(re.findall(r"[a-z]+", value.lower()))


def infer_task_type(description: str) -> str:
    """Infer a task category from its free-text description."""
    lowered = description.lower()
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return task_type
    return "general"


@dataclass(frozen=True)
class KnowledgeEntry:
    """Represent one retrievable knowledge snippet."""

    id: str
    species: str
    task_type: str
    keywords: list[str]
    guidance: str
    source_title: str
    source_url: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "KnowledgeEntry":
        """Create an entry from JSON data."""
        return cls(
            id=str(data.get("id", "")),
            species=str(data.get("species", "general")),
            task_type=str(data.get("task_type", "general")),
            keywords=[str(value) for value in data.get("keywords", [])],
            guidance=str(data.get("guidance", "")),
            source_title=str(data.get("source_title", "")),
            source_url=str(data.get("source_url", "")),
        )


class PetCareKnowledgeBase:
    """Retrieve pet-care guidance from a local knowledge base."""

    def __init__(self, path: str | Path = DEFAULT_KNOWLEDGE_BASE_PATH):
        self.path = Path(path)
        self.entries = self._load_entries()

    def _load_entries(self) -> list[KnowledgeEntry]:
        """Load knowledge snippets from disk."""
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [KnowledgeEntry.from_dict(item) for item in data]

    def retrieve(self, task: "Task", pet_species: str, limit: int = 3) -> list[KnowledgeEntry]:
        """Return the most relevant snippets for a task."""
        inferred_type = infer_task_type(task.description)
        description_words = _normalize_words(task.description)
        scored_entries: list[tuple[int, KnowledgeEntry]] = []

        for entry in self.entries:
            score = 0
            if entry.species == pet_species:
                score += 4
            elif entry.species == "general":
                score += 1
            else:
                continue

            if entry.task_type == inferred_type:
                score += 4
            elif entry.task_type == "general":
                score += 1

            keyword_overlap = len(description_words & set(entry.keywords))
            score += keyword_overlap * 2

            if score > 0:
                scored_entries.append((score, entry))

        scored_entries.sort(key=lambda item: (-item[0], item[1].id))
        return [entry for _, entry in scored_entries[:limit]]


@dataclass(frozen=True)
class PlanningStep:
    """Record an observable intermediate decision during schedule planning."""

    step_number: int
    task_label: str
    task_type: str
    priority: str
    time_remaining_before: int
    checks: list[str]
    decision: str
    reason: str
    suggested_slot: str | None

    def to_dict(self) -> dict[str, object]:
        """Convert the planning step into a UI-friendly dictionary."""
        return {
            "Step": self.step_number,
            "Task": self.task_label,
            "Type": self.task_type.title(),
            "Priority": self.priority.title(),
            "Time Remaining Before": self.time_remaining_before,
            "Checks": " | ".join(self.checks),
            "Decision": self.decision.title(),
            "Reason": self.reason,
            "Suggested Slot": self.suggested_slot or "-",
        }


@dataclass
class Task:
    """Represent one care task for one pet."""

    description: str
    time: str
    duration_minutes: int
    frequency: str = "once"
    completed: bool = False
    due_date: date = field(default_factory=date.today)
    priority: str = "medium"
    pet_name: str = ""

    def mark_complete(self) -> None:
        """Mark the task as complete."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Create the next task when this one recurs."""
        increments = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}
        delta = increments.get(self.frequency)
        if delta is None:
            return None

        return Task(
            description=self.description,
            time=self.time,
            duration_minutes=self.duration_minutes,
            frequency=self.frequency,
            completed=False,
            due_date=self.due_date + delta,
            priority=self.priority,
            pet_name=self.pet_name,
        )

    def to_dict(self) -> dict[str, object]:
        """Convert the task into a JSON-safe dictionary."""
        return {
            "description": self.description,
            "time": self.time,
            "duration_minutes": self.duration_minutes,
            "frequency": self.frequency,
            "completed": self.completed,
            "due_date": self.due_date.isoformat(),
            "priority": self.priority,
            "pet_name": self.pet_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Task:
        """Create a task from saved JSON data."""
        due_date_text = str(data.get("due_date", date.today().isoformat()))
        return cls(
            description=str(data.get("description", "")),
            time=str(data.get("time", "08:00")),
            duration_minutes=int(data.get("duration_minutes", 0)),
            frequency=str(data.get("frequency", "once")),
            completed=bool(data.get("completed", False)),
            due_date=date.fromisoformat(due_date_text),
            priority=str(data.get("priority", "medium")),
            pet_name=str(data.get("pet_name", "")),
        )


@dataclass
class Pet:
    """Store pet details and the pet's tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def task_count(self) -> int:
        """Return how many tasks this pet has."""
        return len(self.tasks)

    def incomplete_tasks(self) -> list[Task]:
        """Return only tasks that are not complete."""
        return [task for task in self.tasks if not task.completed]

    def to_dict(self) -> dict[str, object]:
        """Convert the pet and its tasks into a JSON-safe dictionary."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Pet:
        """Create a pet from saved JSON data."""
        pet = cls(
            name=str(data.get("name", "")),
            species=str(data.get("species", "other")),
            age=int(data.get("age", 0)),
        )
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


class Owner:
    """Store owner information and manage multiple pets."""

    def __init__(self, name: str, available_minutes: int):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet when the name is not already used."""
        existing = self.get_pet(pet.name)
        if existing is None:
            self.pets.append(pet)

    def get_pet(self, pet_name: str) -> Pet | None:
        """Look up a pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Collect tasks across all pets."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def to_dict(self) -> dict[str, object]:
        """Convert the owner and pets into a JSON-safe dictionary."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    def save_to_json(self, path: str | Path) -> None:
        """Save the owner state to JSON."""
        output_path = Path(path)
        output_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Owner:
        """Create an owner from saved JSON data."""
        owner = cls(
            name=str(data.get("name", "Jordan")),
            available_minutes=int(data.get("available_minutes", 60)),
        )
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    @classmethod
    def load_from_json(cls, path: str | Path) -> Owner | None:
        """Load owner state from JSON when the file exists."""
        input_path = Path(path)
        if not input_path.exists():
            return None
        data = json.loads(input_path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


class Scheduler:
    """Retrieve, organize, and explain tasks across pets."""

    def __init__(self, owner: Owner):
        self.owner = owner
        self.plan: list[Task] = []
        self.skipped: list[Task] = []
        self.conflicts: list[str] = []
        self.planning_trace: list[PlanningStep] = []
        self.knowledge_base = PetCareKnowledgeBase()

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by date and time."""
        source = self.owner.get_all_tasks() if tasks is None else tasks
        return sorted(
            source,
            key=lambda task: (
                task.due_date,
                _time_sort_key(task.time),
                task.pet_name.lower(),
                task.description.lower(),
            ),
        )

    def sort_by_priority_then_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by priority first, then by time."""
        source = self.owner.get_all_tasks() if tasks is None else tasks
        return sorted(
            source,
            key=lambda task: (
                PRIORITY_ORDER.get(task.priority, 99),
                task.due_date,
                _time_sort_key(task.time),
                task.pet_name.lower(),
                task.description.lower(),
            ),
        )

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        tasks: list[Task] | None = None,
    ) -> list[Task]:
        """Filter tasks by pet name and completion status."""
        filtered = list(self.owner.get_all_tasks() if tasks is None else tasks)
        if pet_name:
            filtered = [task for task in filtered if task.pet_name == pet_name]
        if completed is not None:
            filtered = [task for task in filtered if task.completed == completed]
        return self.sort_by_time(filtered)

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return warnings for tasks scheduled at the exact same time."""
        source = self.owner.get_all_tasks() if tasks is None else tasks
        grouped: dict[tuple[date, str], list[Task]] = {}
        for task in source:
            if task.completed:
                continue
            key = (task.due_date, task.time)
            grouped.setdefault(key, []).append(task)

        warnings: list[str] = []
        for (task_date, task_time), bucket in sorted(
            grouped.items(),
            key=lambda item: (item[0][0], _time_sort_key(item[0][1])),
        ):
            if len(bucket) < 2:
                continue
            labels = ", ".join(f"{task.pet_name}: {task.description}" for task in bucket)
            warnings.append(
                f"Conflict at {task_time} on {task_date.isoformat()}: {labels}"
            )
        return warnings

    def generate_plan(self, target_date: date | None = None) -> list[Task]:
        """Build a daily schedule that fits inside the available time."""
        target = date.today() if target_date is None else target_date
        candidates = [
            task
            for task in self.owner.get_all_tasks()
            if not task.completed and task.due_date == target
        ]
        sorted_tasks = self.sort_by_priority_then_time(candidates)
        self.conflicts = self.detect_conflicts(sorted_tasks)
        self.plan = []
        self.skipped = []
        self.planning_trace = []
        time_remaining = self.owner.available_minutes

        for step_number, task in enumerate(sorted_tasks, start=1):
            checks = [
                "Task is pending",
                f"Task date matches {target.isoformat()}",
                f"Priority {task.priority} evaluated before lower priority work",
                f"Duration {task.duration_minutes} min compared against {time_remaining} min remaining",
            ]
            task_label = f"{task.pet_name} | {task.time} | {task.description}"
            if task.duration_minutes <= time_remaining:
                self.plan.append(task)
                self.planning_trace.append(
                    PlanningStep(
                        step_number=step_number,
                        task_label=task_label,
                        task_type=infer_task_type(task.description),
                        priority=task.priority,
                        time_remaining_before=time_remaining,
                        checks=checks,
                        decision="scheduled",
                        reason="Fits within remaining time after priority-first sorting.",
                        suggested_slot=task.time,
                    )
                )
                time_remaining -= task.duration_minutes
            else:
                self.skipped.append(task)
                suggested_slot = self.find_next_available_slot(
                    task.duration_minutes,
                    target_date=target,
                    start_time=task.time,
                )
                self.planning_trace.append(
                    PlanningStep(
                        step_number=step_number,
                        task_label=task_label,
                        task_type=infer_task_type(task.description),
                        priority=task.priority,
                        time_remaining_before=time_remaining,
                        checks=checks,
                        decision="skipped",
                        reason="Does not fit within the remaining time budget for the day.",
                        suggested_slot=suggested_slot,
                    )
                )

        return self.plan

    def find_next_available_slot(
        self,
        duration_minutes: int,
        target_date: date | None = None,
        start_time: str = "06:00",
        end_time: str = "22:00",
    ) -> str | None:
        """Find the next open slot that can fit a task duration."""
        target = date.today() if target_date is None else target_date
        busy_tasks = [
            task
            for task in self.owner.get_all_tasks()
            if not task.completed and task.due_date == target
        ]
        ordered = self.sort_by_time(busy_tasks)
        window_start = _minutes_from_time(start_time)
        window_end = _minutes_from_time(end_time)
        current = window_start

        for task in ordered:
            task_start = _minutes_from_time(task.time)
            if task_start - current >= duration_minutes:
                return _time_from_minutes(current)
            task_end = task_start + task.duration_minutes
            if task_end > current:
                current = task_end

        if window_end - current >= duration_minutes:
            return _time_from_minutes(current)
        return None

    def suggest_reschedule_slots(
        self,
        tasks: list[Task] | None = None,
        target_date: date | None = None,
    ) -> dict[str, str | None]:
        """Suggest a next available slot for each skipped or supplied task."""
        source = self.skipped if tasks is None else tasks
        suggestions: dict[str, str | None] = {}
        for task in source:
            label = f"{task.pet_name} | {task.description}"
            suggestions[label] = self.find_next_available_slot(
                task.duration_minutes,
                task.due_date if target_date is None else target_date,
            )
        return suggestions

    def task_guidance(self, task: Task, limit: int = 2) -> list[KnowledgeEntry]:
        """Retrieve guidance entries for a task."""
        pet = self.owner.get_pet(task.pet_name)
        pet_species = "general" if pet is None else pet.species
        return self.knowledge_base.retrieve(task, pet_species, limit=limit)

    def plan_guidance(
        self,
        tasks: list[Task] | None = None,
        limit_per_task: int = 2,
    ) -> dict[str, list[KnowledgeEntry]]:
        """Retrieve guidance grouped by task label."""
        source = self.plan if tasks is None else tasks
        guidance: dict[str, list[KnowledgeEntry]] = {}
        for task in source:
            label = f"{task.pet_name} | {task.time} | {task.description}"
            guidance[label] = self.task_guidance(task, limit=limit_per_task)
        return guidance

    def planning_trace_rows(self) -> list[dict[str, object]]:
        """Return planning-trace rows for display."""
        return [step.to_dict() for step in self.planning_trace]

    def mark_task_complete(
        self,
        pet_name: str,
        description: str,
        time: str,
        due_date: date | None = None,
    ) -> Task | None:
        """Mark a task complete and create the next recurring task if needed."""
        target_date = date.today() if due_date is None else due_date
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return None

        for task in pet.tasks:
            if (
                task.description == description
                and task.time == time
                and task.due_date == target_date
                and not task.completed
            ):
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    pet.add_task(next_task)
                return next_task
        return None

    def explain_plan(self, target_date: date | None = None) -> str:
        """Return a readable summary of the current plan."""
        target = date.today() if target_date is None else target_date
        if not self.plan:
            return f"No tasks could be scheduled for {target.isoformat()}."

        lines = [
            f"Today's schedule for {self.owner.name}",
            f"Date: {target.isoformat()}",
            f"Available time: {self.owner.available_minutes} minutes",
            "",
            "Scheduled tasks:",
        ]

        total = 0
        for task in self.plan:
            lines.append(
                f"- {task.time} | {task.pet_name} | {task.description} | "
                f"{task.duration_minutes} min | {task.frequency} | {task.priority}"
            )
            total += task.duration_minutes

        lines.append("")
        lines.append(f"Total scheduled time: {total} minutes")

        if self.skipped:
            lines.append("")
            lines.append("Skipped tasks:")
            for task in self.skipped:
                guidance = self.task_guidance(task, limit=1)
                guidance_text = ""
                if guidance:
                    guidance_text = f" | guidance: {guidance[0].guidance}"
                lines.append(
                    f"- {task.time} | {task.pet_name} | {task.description} | "
                    f"{task.duration_minutes} min | {task.priority}{guidance_text}"
                )

        if self.conflicts:
            lines.append("")
            lines.append("Conflict warnings:")
            for warning in self.conflicts:
                lines.append(f"- {warning}")

        if self.planning_trace:
            lines.append("")
            lines.append("Agentic planning trace:")
            for step in self.planning_trace:
                slot_text = (
                    f" Suggested slot: {step.suggested_slot}."
                    if step.suggested_slot is not None and step.decision == "skipped"
                    else ""
                )
                lines.append(
                    f"- Step {step.step_number}: {step.task_label} -> {step.decision}. "
                    f"{step.reason}{slot_text}"
                )

        guidance_by_task = self.plan_guidance()
        if guidance_by_task:
            lines.append("")
            lines.append("Retrieved care guidance:")
            for label, entries in guidance_by_task.items():
                if not entries:
                    continue
                lines.append(f"- {label}")
                for entry in entries:
                    lines.append(
                        f"  * {entry.guidance} ({entry.source_title})"
                    )

        return "\n".join(lines)
