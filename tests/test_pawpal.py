from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def make_owner() -> Owner:
    owner = Owner("Jordan", 60)
    owner.add_pet(Pet("Mochi", "dog", 3))
    owner.add_pet(Pet("Luna", "cat", 5))
    return owner


def test_mark_complete_changes_task_status():
    task = Task("Medication", "09:00", 10, "daily", due_date=date.today())
    task.mark_complete()
    assert task.completed is True


def test_adding_task_to_pet_increases_task_count():
    pet = Pet("Mochi", "dog", 3)
    pet.add_task(Task("Breakfast", "08:00", 10, due_date=date.today()))
    assert pet.task_count() == 1


def test_sort_by_time_returns_chronological_order():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    mochi.add_task(Task("Play time", "18:00", 15, due_date=date.today()))
    mochi.add_task(Task("Breakfast", "08:00", 10, due_date=date.today()))
    mochi.add_task(Task("Walk", "07:30", 20, due_date=date.today()))

    scheduler = Scheduler(owner)
    times = [task.time for task in scheduler.sort_by_time()]
    assert times == ["07:30", "08:00", "18:00"]


def test_filter_tasks_can_limit_results_to_one_pet():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    luna = owner.get_pet("Luna")
    assert mochi is not None
    assert luna is not None
    mochi.add_task(Task("Walk", "07:30", 20, due_date=date.today()))
    luna.add_task(Task("Medication", "07:30", 5, due_date=date.today()))

    scheduler = Scheduler(owner)
    filtered = scheduler.filter_tasks(pet_name="Luna", completed=False)
    assert len(filtered) == 1
    assert filtered[0].pet_name == "Luna"


def test_marking_daily_task_complete_creates_next_day_task():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    task = Task("Breakfast", "08:00", 10, "daily", due_date=date.today())
    mochi.add_task(task)

    scheduler = Scheduler(owner)
    new_task = scheduler.mark_task_complete("Mochi", "Breakfast", "08:00", date.today())

    assert new_task is not None
    assert task.completed is True
    assert new_task.due_date == date.today() + timedelta(days=1)
    assert mochi.task_count() == 2


def test_detect_conflicts_flags_duplicate_times():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    luna = owner.get_pet("Luna")
    assert mochi is not None
    assert luna is not None
    mochi.add_task(Task("Walk", "07:30", 20, due_date=date.today()))
    luna.add_task(Task("Medication", "07:30", 5, due_date=date.today()))

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1
    assert "07:30" in conflicts[0]


def test_generate_plan_skips_tasks_after_time_limit():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    mochi.add_task(Task("Walk", "07:30", 30, due_date=date.today()))
    mochi.add_task(Task("Grooming", "08:30", 40, due_date=date.today()))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())

    assert len(plan) == 1
    assert scheduler.skipped[0].description == "Grooming"
