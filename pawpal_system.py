"""Core classes and scheduling logic for the PawPal+ app."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


def _time_sort_key(value: str) -> tuple[int, int]:
    """Convert HH:MM text into a sortable tuple."""
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour, parsed.minute


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


class Scheduler:
    """Retrieve, organize, and explain tasks across pets."""

    def __init__(self, owner: Owner):
        self.owner = owner
        self.plan: list[Task] = []
        self.skipped: list[Task] = []
        self.conflicts: list[str] = []

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
        sorted_tasks = self.sort_by_time(candidates)
        self.conflicts = self.detect_conflicts(sorted_tasks)
        self.plan = []
        self.skipped = []
        time_remaining = self.owner.available_minutes

        for task in sorted_tasks:
            if task.duration_minutes <= time_remaining:
                self.plan.append(task)
                time_remaining -= task.duration_minutes
            else:
                self.skipped.append(task)

        return self.plan

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
                f"{task.duration_minutes} min | {task.frequency}"
            )
            total += task.duration_minutes

        lines.append("")
        lines.append(f"Total scheduled time: {total} minutes")

        if self.skipped:
            lines.append("")
            lines.append("Skipped tasks:")
            for task in self.skipped:
                lines.append(
                    f"- {task.time} | {task.pet_name} | {task.description} | "
                    f"{task.duration_minutes} min"
                )

        if self.conflicts:
            lines.append("")
            lines.append("Conflict warnings:")
            for warning in self.conflicts:
                lines.append(f"- {warning}")

        return "\n".join(lines)
