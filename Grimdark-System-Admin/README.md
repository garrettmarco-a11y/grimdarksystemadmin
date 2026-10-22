# Grimdark System Admin

A Python/Tkinter prototype of a grimdark space-feudal administration simulation. The player governs a troubled hive city through subordinate agents, task assignments, resources, time advancement, Imperial tribute, and events.

This repository is being organized for incremental development with Git and a coding agent. The guiding rule is to keep the game playable while adding systems in small, tested steps.

## Current status

- Working baseline: the existing single-file Python/Tkinter prototype.
- Simulation includes subordinate skill dice, task assignment and progress, resource inventories, daily ticks, tribute, and random events.
- A deterministic five-tick `Test Action: Administrative Audit` is included to validate the task lifecycle.
- The simulation and GUI are still in one Python module. Separating them is a planned refactor, not a prerequisite for running the current version.
- The GUI has been reported as working on the user's machine. Automated tests cover selected simulation behavior; the GUI is not covered by automated UI tests.

## Requirements

- Python 3.10 or newer recommended.
- Tkinter, which is included with many standard Python installations. On some Linux distributions it is provided by a separate OS package.
- No third-party Python dependencies are currently required.

## Run

From the repository root:

```bash
python src/grimdark_system_admin.py
```

If `python` points to Python 2 or is unavailable, use `python3` on macOS/Linux or `py -3` on Windows.

## Test

```bash
python -m unittest discover -s tests -v
```

The tests use only Python's standard library.

## Project guide

- `AGENTS.md` — operating instructions for coding agents.
- `docs/GAME_DESIGN.md` — current concept and boundaries between implemented systems and future design.
- `docs/ROADMAP.md` — staged development plan and current milestone.
- `docs/ARCHITECTURE.md` — current code shape and intended direction.
- `docs/WORKFLOW.md` — recommended Git and coding-agent workflow.
- `docs/DECISIONS.md` — decisions already made and open questions.

## First development milestone

Preserve the current working loop. Improve the code's testability and separation of concerns before adding large new systems. The next gameplay addition proposed for after that cleanup is a simple food inventory/production action, but it should be implemented only as a small, tested feature.

## Git quick start

```bash
git init
git add .
git commit -m "chore: establish playable Python prototype"
```

Create a private or public GitHub repository as appropriate, then follow GitHub's instructions for adding the remote and pushing the initial branch. Do not commit local save data, credentials, virtual environments, or editor caches.
