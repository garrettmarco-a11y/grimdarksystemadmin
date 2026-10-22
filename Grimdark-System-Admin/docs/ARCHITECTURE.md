# Architecture Notes

## Current structure

The current implementation is in `src/grimdark_system_admin.py`. It contains both simulation classes and the Tkinter UI.

Simulation-oriented classes currently include:
- `DiceType`, `ResourceType`, `GovernanceArea`
- `DicePool`
- `Subordinate`
- `Task`
- `Resources`
- `GameState`

The UI is managed by `GDSAGui`; `main()` constructs the Tkinter root and starts the event loop.

## Current constraints

- Simulation and presentation are coupled in one module.
- The game state uses randomness directly, which can make some tests nondeterministic.
- The UI has not been covered by automated interaction tests.
- There is no defined save/load contract yet. Imported `json` and dataclass utilities should not be taken as proof that save/load is implemented.
- Some mechanics are placeholders and may change as the design develops.

## Intended direction

Refactor in small steps, keeping the app runnable after each change. A reasonable future separation is:

- `gdsa/models.py` — enums and data structures.
- `gdsa/simulation.py` — game state and rules.
- `gdsa/ui.py` — Tkinter widgets and presentation.
- `gdsa/app.py` — application entry point.

This is a target, not a requirement to move every class immediately. First identify clean boundaries, add tests, then extract code with behavior-preserving changes.

## Architectural rules

- The simulation should not require a Tkinter root to advance time or resolve actions.
- UI code should call simulation methods and render their results, not independently implement game rules.
- Keep random-number use in simulation code; consider injecting a random generator when it becomes useful for reproducible tests.
- Keep display strings and internal identifiers distinct when a behavior requires stable identity.
- Avoid introducing frameworks or external dependencies without a concrete need.
