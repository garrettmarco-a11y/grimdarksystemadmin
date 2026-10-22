# Instructions for Coding Agents

## Project goal

Maintain and incrementally improve **Grimdark System Admin**, a Python/Tkinter simulation about governing a troubled hive city in a decaying space-feudal empire.

## Source of truth

Before changing code, read:
1. `README.md`
2. `docs/GAME_DESIGN.md`
3. `docs/ROADMAP.md`
4. `docs/ARCHITECTURE.md`
5. The relevant code and tests

The implementation is the `src/gdsa/` package: simulation rules in `models.py` and `simulation.py` (no Tkinter), presentation in `ui.py`, entry point in `app.py`. `src/grimdark_system_admin.py` is a thin launcher. Do not assume the missing GameMaker project exists.

## Working rules

- Make the smallest coherent change that meets the task.
- Preserve existing behavior unless the task explicitly calls for changing it.
- Do not silently invent or finalize game-design rules. If a rule is undecided, identify the uncertainty and either ask or isolate the choice behind a simple, documented implementation.
- Do not add dependencies without explaining why they are needed.
- Keep simulation rules independent of Tkinter when practical. Avoid adding game logic directly to GUI event handlers.
- Add or update tests for simulation changes.
- Run `python -m unittest discover -s tests -v` after changes, plus syntax/compile checks where useful.
- Report exactly which checks ran and whether they passed. Never claim the GUI was tested interactively unless it actually was.
- Avoid broad rewrites, premature plugin systems, unnecessary abstractions, and speculative features.
- Do not add economy, population, ideology, senate, AGI, or narrative systems merely because they appear in the long-term design. Follow the current milestone in `docs/ROADMAP.md`.
- Keep player-facing text consistent with the grimdark setting, but prioritize clear UI feedback.

## Change protocol

1. Inspect relevant code and current Git status.
2. Summarize the proposed change and likely files affected before a non-trivial implementation.
3. Implement on a focused branch when using Git.
4. Write regression tests.
5. Run tests and inspect the diff.
6. Summarize behavior changes, tests, known limitations, and any decisions left open.
7. Do not commit, push, publish a repository, or open a pull request unless the user explicitly asks.

## Completion checklist

- [ ] Scope stayed within the requested milestone.
- [ ] Tests cover the changed behavior where feasible.
- [ ] Existing tests pass.
- [ ] No unrelated files or generated artifacts were added.
- [ ] Documentation reflects any behavior or workflow change.
