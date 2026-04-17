# PawPal+ Project Reflection

## 1. System Design

### Core user actions

The three main actions in my system are:

- add a pet for one owner
- add care tasks to a specific pet
- generate and review today's schedule

**a. Initial design**

I started with 4 classes for the PawPal+ system.

- **Owner** stores the owner's name, available time, and the pets they manage.
- **Pet** stores the pet's basic details and the tasks for that pet.
- **Task** stores one care item with a time, duration, frequency, and completion status.
- **Scheduler** reads tasks from the owner, sorts them, filters them, checks for conflicts, and builds the daily plan.

I chose these classes because they each had one clear job. This made the system easier to understand before I wrote the real logic.

**b. Design changes**

Yes, the design changed during implementation.

At first, the project only worked with one pet and very simple tasks. Later I changed `Owner` so it could manage multiple pets. I also changed `Task` so it could store a task time, a frequency like daily or weekly, and a completion status. I changed the `Scheduler` too, because it needed methods for sorting, filtering, conflict detection, and recurrence. I made these changes because the assignment needed a smarter system than the first draft.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler looks at the task date, task time, completion status, and the owner's available minutes for the day. It first sorts the tasks by time. Then it adds tasks into the plan until there is no more time left.

I treated available time as the hard limit because a schedule should not go past the time the owner actually has. I also kept completion status important so finished tasks do not keep showing up in the active plan.

**b. Tradeoffs**

One tradeoff in my scheduler is that conflict detection only checks exact time matches. It does not calculate overlapping durations like a task from 8:00 to 8:30 and another from 8:15 to 8:45.

I think this tradeoff is reasonable for this version because it keeps the logic simple and easy to explain. It still catches a common scheduling problem without making the code too complex for this project.

## 3. AI Collaboration

**a. How I used AI**

I used AI for design brainstorming, class planning, test ideas, and cleanup. The most helpful prompts were short and direct, like asking what methods the scheduler should have, how to sort times in `HH:MM` format, and what edge cases should be tested.

Copilot was most useful when I was moving from one phase to the next. It helped me turn the UML idea into code structure, and later helped me think about what tests mattered most.

**b. Judgment and verification**

I did not accept every AI idea exactly as it was given. One example was the early idea to keep the scheduler very simple and only work with one pet. I changed that idea because the assignment expected the owner to manage multiple pets and for the scheduler to work across all of them.

I checked the suggestions by reading the code carefully, running the CLI demo, and running `python -m pytest`. If the suggestion made the code harder to understand or did not match the project instructions, I changed it.

**c. Organization with separate chat sessions**

Using separate chat sessions helped me stay organized because each phase had a different goal. One chat could stay focused on system design, another on algorithms, and another on testing. This made it easier to compare ideas without mixing everything together.

**d. Lead architect takeaway**

My biggest lesson was that I still had to be the lead architect even when AI was helping. AI could suggest code fast, but I still had to decide what belonged in the system, what was too much, and what needed to be tested. The final responsibility was still mine.

## 4. Testing and Verification

**a. What I tested**

I tested task completion, task addition, sorting by time, filtering by pet, recurring daily task creation, conflict detection, and schedule generation when time runs out.

These tests were important because they cover the main behaviors the app depends on. If one of these breaks, the schedule shown to the user could be confusing or wrong.

**b. Confidence**

My confidence level is 4 out of 5. The most important behaviors now have automated tests, and the results pass.

If I had more time, I would test more edge cases. I would test overlapping durations, editing tasks after they are created, and more date combinations for weekly recurrence.

## 5. Reflection

**a. What went well**

I am most satisfied with the way the backend classes work together now. The owner can manage multiple pets, each pet can keep its own tasks, and the scheduler can work across all of them in one place.

**b. What I would improve**

If I had another iteration, I would improve the UI more. I would let the user edit or delete tasks, and I would show better calendar-style output instead of only tables and text.

**c. Key takeaway**

I learned that planning the system first made the coding part much easier. I also learned that AI works best when I give it a clear goal and then verify the result myself.
