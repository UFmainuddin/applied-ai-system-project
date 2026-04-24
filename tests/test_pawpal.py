from datetime import date, timedelta
from pathlib import Path

from pawpal_system import Owner, Pet, Scheduler, Task, infer_task_type


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
    mochi.add_task(Task("Walk", "08:30", 30, due_date=date.today(), priority="low"))
    mochi.add_task(Task("Medication", "07:30", 40, due_date=date.today(), priority="high"))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())

    assert len(plan) == 1
    assert plan[0].description == "Medication"
    assert scheduler.skipped[0].description == "Walk"


def test_priority_sorting_happens_before_time_in_daily_plan():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    mochi.add_task(Task("Low priority walk", "07:00", 15, due_date=date.today(), priority="low"))
    mochi.add_task(Task("High priority medication", "09:00", 15, due_date=date.today(), priority="high"))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())

    assert plan[0].description == "High priority medication"


def test_find_next_available_slot_returns_open_gap():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    mochi.add_task(Task("Walk", "08:00", 20, due_date=date.today()))
    mochi.add_task(Task("Breakfast", "09:00", 15, due_date=date.today()))

    scheduler = Scheduler(owner)
    slot = scheduler.find_next_available_slot(30, date.today(), start_time="08:00", end_time="12:00")

    assert slot == "08:20"


def test_owner_can_save_and_load_json():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    mochi.add_task(Task("Breakfast", "08:00", 10, "daily", due_date=date.today(), priority="high"))

    file_path = Path("test_owner_data.json")
    owner.save_to_json(file_path)
    loaded = Owner.load_from_json(file_path)

    assert loaded is not None
    assert loaded.name == "Jordan"
    assert loaded.get_pet("Mochi") is not None
    loaded_mochi = loaded.get_pet("Mochi")
    assert loaded_mochi is not None
    assert loaded_mochi.tasks[0].description == "Breakfast"


def test_infer_task_type_detects_medication_tasks():
    assert infer_task_type("Morning medication") == "medication"


def test_rag_retrieves_species_and_task_guidance():
    owner = make_owner()
    luna = owner.get_pet("Luna")
    assert luna is not None
    task = Task("Medication", "08:00", 5, due_date=date.today(), priority="high")
    luna.add_task(task)

    scheduler = Scheduler(owner)
    guidance = scheduler.task_guidance(task)

    assert guidance
    assert any("Medication" in entry.source_title or "medication" in entry.guidance.lower() for entry in guidance)


def test_explain_plan_includes_retrieved_guidance_section():
    owner = make_owner()
    mochi = owner.get_pet("Mochi")
    assert mochi is not None
    mochi.add_task(Task("Morning walk", "08:00", 20, due_date=date.today(), priority="high"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan(date.today())
    explanation = scheduler.explain_plan(date.today())

    assert "Retrieved care guidance:" in explanation
    assert "ASPCA General Dog Care" in explanation
