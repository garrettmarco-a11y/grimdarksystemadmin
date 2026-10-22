# Git and Coding-Agent Workflow

## One-time local setup

The repository is hosted on GitHub. Clone it and run the tests from the repository root:

```bash
git clone <your-repository-url>
cd <repository-folder>
python -m unittest discover -s tests -v
```

Do not paste access tokens into source files or commit them.

## Normal feature cycle

1. Start from an up-to-date `main`.
2. Create a focused branch, e.g. `feat/food-production-task` or `refactor/separate-simulation`.
3. Give the coding agent one bounded task with acceptance criteria.
4. Ask it to inspect the code and tests before editing.
5. Review the diff and run the test suite.
6. Launch the GUI for changes that affect the UI.
7. Commit the change with a descriptive message.
8. Merge through a pull request if using GitHub, or merge locally if working solo.

## Suggested branch prefixes

- `feat/` — new behavior.
- `fix/` — bug fix.
- `refactor/` — behavior-preserving structural change.
- `test/` — tests only.
- `docs/` — documentation and workflow.

## Good coding-agent task format

Include:
- **Goal:** one sentence.
- **Context:** relevant design and architecture notes.
- **Acceptance criteria:** observable behavior, preferably checkable.
- **Constraints:** what must not change.
- **Validation:** exact commands to run.

Example:

> Goal: Make the task lifecycle rules independently testable without creating a Tkinter window.
>
> Read `AGENTS.md`, `docs/ARCHITECTURE.md`, and the existing tests first. Propose a small extraction plan before editing.
>
> Acceptance criteria:
> - The app still launches using the README command.
> - The five-tick audit still completes exactly on tick five.
> - The agent is released after completion.
> - Existing task progression behavior is preserved.
> - All tests pass using `python -m unittest discover -s tests -v`.
>
> Constraints: Do not add dependencies or implement new gameplay systems. Do not change balancing values unless necessary and explicitly justified.

## Review checklist

- Does the change stay within the current milestone?
- Are behavior changes intentional and documented?
- Are tests present for changed rules?
- Did the documented test command pass?
- Was the GUI manually checked if it was affected?
- Does the diff contain unrelated edits?
- Are unresolved design choices called out rather than guessed?
