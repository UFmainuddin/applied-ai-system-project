# PawPal+ UML Class Diagram

```mermaid
classDiagram
    class Owner {
        +name: str
        +available_minutes: int
        +pets: list[Pet]
        +add_pet(pet)
        +get_pet(pet_name)
        +get_all_tasks()
    }

    class Pet {
        +name: str
        +species: str
        +age: int
        +tasks: list[Task]
        +add_task(task)
        +task_count()
        +incomplete_tasks()
    }

    class Task {
        +description: str
        +time: str
        +duration_minutes: int
        +frequency: str
        +completed: bool
        +due_date: date
        +priority: str
        +pet_name: str
        +mark_complete()
        +next_occurrence()
    }

    class Scheduler {
        +owner: Owner
        +plan: list[Task]
        +skipped: list[Task]
        +conflicts: list[str]
        +sort_by_time(tasks)
        +filter_tasks(pet_name, completed, tasks)
        +detect_conflicts(tasks)
        +generate_plan(target_date)
        +mark_task_complete(pet_name, description, time, due_date)
        +explain_plan(target_date)
    }

    Owner "1" --> "many" Pet : manages
    Pet "1" --> "many" Task : stores
    Scheduler --> Owner : uses
    Scheduler --> Task : sorts and filters
```

## Relationships

- One `Owner` can manage many pets.
- Each `Pet` stores its own list of tasks.
- `Scheduler` works across all pets by reading tasks from the owner.
- `Task` supports recurrence through `next_occurrence()`.

## Final Diagram Asset

The exported diagram image for the project is saved as `uml_final.png`.
