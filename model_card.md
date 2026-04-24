# PawPal+ Model Card

## System Summary

PawPal+ is a local applied AI system for pet care planning. It combines retrieval from a pet-care knowledge base, a priority-based scheduler, an observable planning trace, and a specialized pet-care briefing layer.

## Intended Use

- Help an owner organize daily pet-care tasks across multiple pets.
- Explain why tasks were scheduled or skipped.
- Surface high-level care reminders from trusted pet-care sources.
- Demonstrate applied AI system design for an academic portfolio project.

## Out of Scope

- Medical diagnosis
- Medication dosing advice
- Emergency care instructions
- Replacing veterinary guidance

## Data Sources

- Local `knowledge_base.json`
- Source links paraphrased from ASPCA and Cornell Feline Health Center materials

## Reliability Summary

- `19/19` pytest tests passed in the final version.
- `4/4` evaluation-harness checks passed in `evaluate_pawpal.py`.
- Guardrails reject invalid priorities, invalid frequencies, and non-positive durations.

## Limitations and Biases

- The knowledge base is small and manually curated, so coverage is limited.
- Retrieval is keyword-based and may miss relevant guidance if a task description uses unexpected wording.
- Conflict detection only checks exact start-time matches, not overlapping durations.
- Advice is biased toward the specific public sources included in the local knowledge base.

## Misuse Risks and Mitigations

- A user could treat the tool like veterinary advice. To reduce that risk, the specialized summary uses caution language for medication and vet tasks.
- A user could overtrust skipped-task suggestions. The system labels them as suggestions, not guarantees.
- A user could enter poor task data. Guardrails now reject invalid priorities, invalid frequencies, and zero-length durations.

## What Surprised Me During Testing

The most useful surprise was how much easier the system became to debug once the planning trace was visible. The biggest non-logic issue I hit was pytest trying to collect an inaccessible cache directory, which led me to tighten test discovery with `pytest.ini`.

## AI Collaboration Reflection

One helpful AI suggestion was to implement the RAG layer with a local JSON knowledge base first instead of reaching for a heavier external retrieval stack. That made the project reproducible and easy to test.

One flawed suggestion earlier in the project direction was leaning too much on “AI-powered” wording without enough observable system behavior behind it. I corrected that by adding the planning trace, specialization layer, and evaluation harness so the system behavior is inspectable and measurable.

## Ethical Position

PawPal+ should be treated as a scheduling and explanation tool, not a diagnostic one. The system is most responsible when it helps users stay organized, flags uncertainty around medication or vet-related timing, and encourages veterinarian follow-up instead of pretending to offer clinical certainty.
