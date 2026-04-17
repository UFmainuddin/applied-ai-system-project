from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


st.set_page_config(page_title="PawPal+", page_icon="P", layout="centered")


DEFAULT_PET = Pet("Mochi", "dog", 3)
DEFAULT_PET.add_task(Task("Morning walk", "08:00", 20, "daily", due_date=date.today()))
DEFAULT_PET.add_task(Task("Breakfast", "08:30", 10, "daily", due_date=date.today()))
DEFAULT_PET.add_task(Task("Vet reminder", "15:00", 30, "once", due_date=date.today()))


if "owner" not in st.session_state:
    owner = Owner("Jordan", 90)
    owner.add_pet(DEFAULT_PET)
    st.session_state.owner = owner


owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)


def time_to_string(value: time) -> str:
    return value.strftime("%H:%M")


def pet_rows() -> list[dict[str, object]]:
    return [
        {
            "Pet": pet.name,
            "Species": pet.species,
            "Age": pet.age,
            "Tasks": pet.task_count(),
        }
        for pet in owner.pets
    ]


def task_rows(tasks: list[Task]) -> list[dict[str, object]]:
    return [
        {
            "Pet": task.pet_name,
            "Task": task.description,
            "Date": task.due_date.isoformat(),
            "Time": task.time,
            "Duration": task.duration_minutes,
            "Frequency": task.frequency,
            "Status": "Done" if task.completed else "Pending",
        }
        for task in tasks
    ]


st.title("PawPal+")
st.markdown(
    "A pet care planner that tracks multiple pets, sorts tasks by time, "
    "flags conflicts, and handles recurring care tasks."
)

st.divider()

st.subheader("Owner Setup")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Available minutes today",
            min_value=15,
            max_value=720,
            value=owner.available_minutes,
            step=15,
        )
    )

st.divider()

st.subheader("Add a Pet")
with st.form("pet_form"):
    pet_name = st.text_input("Pet name")
    pet_species = st.selectbox("Species", ["dog", "cat", "bird", "other"])
    pet_age = st.number_input("Age", min_value=0, max_value=30, value=1)
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    if not pet_name.strip():
        st.warning("Enter a pet name before adding a pet.")
    elif owner.get_pet(pet_name.strip()) is not None:
        st.warning("That pet name already exists.")
    else:
        owner.add_pet(Pet(pet_name.strip(), pet_species, int(pet_age)))
        st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    st.table(pet_rows())
else:
    st.info("Add at least one pet to start building a schedule.")

st.divider()

st.subheader("Add a Task")
if not owner.pets:
    st.info("Create a pet first so tasks have a place to go.")
else:
    with st.form("task_form"):
        selected_pet = st.selectbox("Pet", [pet.name for pet in owner.pets])
        description = st.text_input("Task description", value="Evening walk")
        task_date = st.date_input("Task date", value=date.today())
        task_time = st.time_input("Task time", value=time(18, 0))
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, value=20, step=5)
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        add_task = st.form_submit_button("Add task")

    if add_task:
        pet = owner.get_pet(selected_pet)
        if pet is None:
            st.error("Selected pet was not found.")
        elif not description.strip():
            st.warning("Enter a task description before adding a task.")
        else:
            pet.add_task(
                Task(
                    description=description.strip(),
                    time=time_to_string(task_time),
                    duration_minutes=int(duration),
                    frequency=frequency,
                    due_date=task_date,
                    priority=priority,
                )
            )
            st.success(f"Added task for {selected_pet}.")

st.divider()

st.subheader("Task List")
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    pet_filter = st.selectbox("Filter by pet", ["All pets"] + [pet.name for pet in owner.pets])
with filter_col2:
    status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

selected_completed = None
if status_filter == "Pending":
    selected_completed = False
elif status_filter == "Completed":
    selected_completed = True

selected_pet_name = None if pet_filter == "All pets" else pet_filter
filtered_tasks = scheduler.filter_tasks(pet_name=selected_pet_name, completed=selected_completed)

if filtered_tasks:
    st.table(task_rows(filtered_tasks))
else:
    st.info("No tasks match the current filters.")

st.divider()

st.subheader("Mark a Task Complete")
pending_tasks = scheduler.filter_tasks(completed=False)
if not pending_tasks:
    st.info("There are no pending tasks right now.")
else:
    task_labels = {
        f"{task.pet_name} | {task.due_date.isoformat()} | {task.time} | {task.description}": task
        for task in pending_tasks
    }
    selected_label = st.selectbox("Pending task", list(task_labels))
    if st.button("Complete selected task"):
        chosen_task = task_labels[selected_label]
        new_task = scheduler.mark_task_complete(
            chosen_task.pet_name,
            chosen_task.description,
            chosen_task.time,
            chosen_task.due_date,
        )
        st.success("Task marked complete.")
        if new_task is not None:
            st.info(
                "Recurring task created for "
                f"{new_task.due_date.isoformat()} at {new_task.time}."
            )

st.divider()

st.subheader("Today's Schedule")
schedule_date = st.date_input("Schedule date", value=date.today(), key="schedule_date")
if st.button("Generate schedule"):
    plan = scheduler.generate_plan(schedule_date)
    st.success("Schedule generated.")

    if scheduler.conflicts:
        for warning in scheduler.conflicts:
            st.warning(warning)

    if plan:
        st.table(task_rows(plan))
    else:
        st.info("No pending tasks were scheduled for that date.")

    if scheduler.skipped:
        st.markdown("### Skipped Tasks")
        st.table(task_rows(scheduler.skipped))

    st.markdown("### Explanation")
    st.text(scheduler.explain_plan(schedule_date))

st.caption(
    "Tasks are kept in Streamlit session state during your current browser session. "
    "Recurring tasks are added automatically when daily or weekly tasks are marked complete."
)
