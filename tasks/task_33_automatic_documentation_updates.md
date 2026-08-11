# 📌 TASK 33 — Automatic Documentation Updates on Feature Changes (`#auto-documentation`)

## Overview
Whenever a **major feature**, **new UI screen**, **agent capability**, or **pipeline change** is added, documentation MUST be updated automatically as part of the same sprint task — no separate manual doc ticket required.

---

## Mandatory Documents to Update

| Document | When to update |
|----------|----------------|
| [`README.md`](../README.md) | New features, launchers, test counts, UI routes — **preserve LLM table** |
| [`tasks.md`](../tasks.md) | New task spec files or section changes |
| [`tasks/task_*.md`](../tasks/) | Feature-specific behavior, acceptance criteria |
| [`docs/AGENT_PIPELINE_USER_GUIDE.md`](../docs/AGENT_PIPELINE_USER_GUIDE.md) | Pipeline, UI navigation, agent status changes |
| [`docs/AgenticOps_AI_Overview.pptx`](../docs/AgenticOps_AI_Overview.pptx) | Major releases — **replace in place** via sync script (one file only) |
| [`docs/AgenticOps_AI_Documentation.docx`](../docs/AgenticOps_AI_Documentation.docx) | Full platform doc — Word format, synced with PPTX |
| [`docs/doc_content.py`](../docs/doc_content.py) | **Single source of truth** for PPTX + DOCX content |
| [`tests/TEST_CASES.xlsx`](../tests/TEST_CASES.xlsx) | New test cases — via `generate_test_excel.py` |

---

## Regeneration Commands

```bash
# Sync ALL documentation — replaces PPTX + DOCX in place (do not create duplicate files)
python docs/sync_all_documentation.py

# Excel test matrix (after test run)
python tests/generate_test_excel.py --unit-passed true --browser-passed true

# Documentation sync check (lists stale doc hints)
python scripts/sync_documentation.py
```

---

## Agent / Builder Directive

After implementing any user-visible feature:

1. Update relevant `tasks/*.md` spec with acceptance criteria
2. Add or extend browser test cases (static or dynamic sprint generator)
3. Update `README.md` feature list (do not modify agent LLM table)
4. Update `docs/AGENT_PIPELINE_USER_GUIDE.md` and `docs/doc_content.py` if pipeline or UI navigation changed
5. Run `python docs/sync_all_documentation.py` to regenerate PPTX + DOCX
6. Regenerate `TEST_CASES.xlsx` after tests pass

---

## Definition: Major Change

- New page/route (e.g. `/agents`, `/sprints`)
- New autonomous pipeline stage or agent behavior
- New test category or dynamic sprint test generation
- Breaking change to startup scripts or ports
- New Plane pickup rules or quality gates

Minor bug fixes with no user-visible impact do not require PPTX regeneration.

---

## Related Tasks

- [`section_1_mandatory_tasks.md`](section_1_mandatory_tasks.md) — README maintenance mandate
- [`task_32_application_uptime_and_sprint_pipeline.md`](task_32_application_uptime_and_sprint_pipeline.md)
- [`section_5_testing_and_quality_gates.md`](section_5_testing_and_quality_gates.md)
