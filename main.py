from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_owner() -> Owner:
    owner = Owner("Jordan", 90)

    mochi = Pet("Mochi", "dog", 3)
    mochi.add_task(Task("Morning walk", "07:30", 20, "daily", due_date=date.today()))
    mochi.add_task(Task("Breakfast", "08:00", 10, "daily", due_date=date.today()))

    luna = Pet("Luna", "cat", 5)
    luna.add_task(Task("Medication", "07:30", 5, "daily", due_date=date.today()))
    luna.add_task(Task("Play time", "18:00", 15, "once", due_date=date.today()))

    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


def main() -> None:
    owner = build_demo_owner()
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())

    print("Today's Schedule")
    print("================")
    for task in plan:
        print(
            f"{task.time} | {task.pet_name} | {task.description} | "
            f"{task.duration_minutes} min | {task.frequency}"
        )

    if scheduler.conflicts:
        print("\nConflict Warnings")
        print("=================")
        for warning in scheduler.conflicts:
            print(warning)

    print("\nFiltered Tasks For Mochi")
    print("========================")
    for task in scheduler.filter_tasks(pet_name="Mochi", completed=False):
        print(f"{task.time} | {task.description}")

    print("\nExplanation")
    print("===========")
    print(scheduler.explain_plan(date.today()))


if __name__ == "__main__":
    main()
