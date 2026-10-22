# Grimdark System Admin

A Python/Tkinter prototype of a grimdark space-feudal administration simulation. The player governs a troubled hive city through subordinate agents, task assignments, resources, time advancement, Imperial tribute, and events.

This repository is being organized for incremental development with Git and a coding agent. The guiding rule is to keep the game playable while adding systems in small, tested steps.

## Current status

- Working baseline: the existing single-file Python/Tkinter prototype.
- Simulation includes subordinate skill dice (rolled weekly), task assignment and progress, resource inventories, daily ticks, daily food upkeep, a repeatable food-production action, tribute, and random events.
- A deterministic five-tick `Test Action: Administrative Audit` is included to validate the task lifecycle.
- Simulation logic lives in a Tkinter-free package (`src/gdsa/`), so the tests run without a display or a Tkinter install.
- Automated tests cover the simulation rules; the GUI is not covered by automated UI tests and should be checked by launching it.

## Requirements

- Python 3.10 or newer recommended.
- Tkinter, which is included with many standard Python installations. On some Linux distributions it is provided by a separate OS package.
- No third-party Python dependencies are currently required.

## Run

From the repository root:

```bash
python src/grimdark_system_admin.py
```

Equivalently: `PYTHONPATH=src python -m gdsa`.

If `python` points to Python 2 or is unavailable, use `python3` on macOS/Linux or `py -3` on Windows.

## Test

```bash
python -m unittest discover -s tests -v
```

The tests use only Python's standard library and do not require Tkinter.

## Layout

```
src/grimdark_system_admin.py   launcher (keeps the documented run command)
src/gdsa/models.py             enums, dice pools, subordinates, tasks, resources
src/gdsa/simulation.py         GameState, tick rules, starting tasks (no Tkinter)
src/gdsa/ui.py                 Tkinter GUI
src/gdsa/app.py                entry point (main)
tests/                         unittest suite
```

## Project guide

- `AGENTS.md` — operating instructions for coding agents.
- `docs/GAME_DESIGN.md` — current concept and boundaries between implemented systems and future design.
- `docs/ROADMAP.md` — staged development plan and current milestone.
- `docs/ARCHITECTURE.md` — current code shape and intended direction.
- `docs/WORKFLOW.md` — recommended Git and coding-agent workflow.
- `docs/DECISIONS.md` — decisions already made and open questions.

## Next development milestone

Simulation and GUI are now separated (a Stage B entry criterion). The next proposed gameplay addition is a simple food inventory/production action, implemented as a small, tested feature once its acceptance criteria are agreed. See `docs/ROADMAP.md`.

Do not commit local save data, credentials, virtual environments, or editor caches; `.gitignore` covers the common cases.
