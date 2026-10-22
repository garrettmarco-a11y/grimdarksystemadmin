# Architecture Notes

## Current structure

```
src/grimdark_system_admin.py   thin launcher for `python src/grimdark_system_admin.py`
src/gdsa/__main__.py           allows `python -m gdsa` (with `src` on the path)
src/gdsa/models.py             DiceType, ResourceType, GovernanceArea, DicePool, Subordinate, Task, Resources
src/gdsa/simulation.py         GameState (tick rules, tribute, events) and add_starting_tasks()
src/gdsa/ui.py                 GDSAGui: Tkinter widgets, automation timer, rendering
src/gdsa/app.py                main(): builds the Tk root and starts the event loop
```

`models.py` and `simulation.py` must not import Tkinter; `tests/test_simulation_rules.py` enforces this. The GUI reads `GameState` and calls its methods. Per-tick results the UI needs to react to (currently `GameState.tribute_outcome`) are exposed as state rather than recomputed by the UI.

The package was extracted from the original single-file baseline without changing simulation behavior; a seeded multi-run comparison of full game state and event logs matched exactly.

## Current constraints

- The game state uses the global `random` module directly; tests control it by patching `gdsa.simulation.random` / `gdsa.models.random`.
- The UI has not been covered by automated interaction tests.
- There is no defined save/load contract yet. Imported `json` and dataclass utilities should not be taken as proof that save/load is implemented.
- Some mechanics are placeholders and may change as the design develops.

## Intended direction

Keep changes small and the app runnable after each one. Likely next structural steps, only when a feature needs them:

- Inject a `random.Random` instance into `GameState` when seeded, reproducible tests become useful.
- Give tasks and subordinates stable IDs separate from display names (names are currently used as identifiers).
- Split `simulation.py` by system (e.g. tribute, events) once it grows; avoid doing so speculatively.

## Architectural rules

- The simulation should not require a Tkinter root to advance time or resolve actions.
- UI code should call simulation methods and render their results, not independently implement game rules.
- Keep random-number use in simulation code; consider injecting a random generator when it becomes useful for reproducible tests.
- Keep display strings and internal identifiers distinct when a behavior requires stable identity.
- Avoid introducing frameworks or external dependencies without a concrete need.
