# Grimdark System Admin

A Python/Tkinter prototype of a grimdark space-feudal administration simulation. The player governs a troubled hive city through subordinate agents, task assignments, resources, time advancement, Imperial tribute, and events.

This repository is being organized for incremental development with Git and a coding agent. The guiding rule is to keep the game playable while adding systems in small, tested steps.

## Current status

- The simulation and GUI are separated into a small package under `src/gdsa/`.
- The game starts paused and advances in daily ticks when the player chooses to run it.
- Agents can be assigned tasks that take time, occupy the agent, and report completion.
- Current resource-linked actions are `Requisition Food Stores` (gain 10 Biologics after five ticks), `Commission Emergency Food Convoy` (spend 10 Materials to gain 20 Biologics after five ticks), and `Restore Order in the Lower Hab-Blocks` (spend 5 Materials to suppress the next Food Riots event after five ticks).
- `Test Action: Administrative Audit` remains available as a deterministic five-tick task for checking the task lifecycle.
- The prototype has daily resource generation, Imperial tribute, placeholder random events, and a limited food upkeep: every 7 days (Day 7, 14, 21, ...) the hive consumes 10 Biologics, taking only what is in store, with shortages logged. Hidden population groups react to whether they were fed; the player sees only a broad public-order status. It does not simulate starvation, population change, or a full supply chain.
- Simulation logic is separated from Tkinter so the standard-library test suite can run without a display. Automated tests cover the simulation rules; the GUI should also be checked by launching it.

The current development focus is Stage B: making administrative actions produce understandable trade-offs without prematurely building the full economy. Before adding another mechanic, decide what the next playable loop should demonstrate and when the test action can be retired. See `docs/ROADMAP.md` and `docs/DECISIONS.md`.

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

For development, `python src/grimdark_system_admin.py --debug` adds a read-only "DEBUG: Population" tab that shows the hidden population state.

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

Do not commit local save data, credentials, virtual environments, or editor caches; `.gitignore` covers the common cases.
