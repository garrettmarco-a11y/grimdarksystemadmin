# Decisions and Open Questions

This file distinguishes current working decisions from matters that still need discussion.

## Working decisions

- **Implementation platform:** Continue with the surviving Python/Tkinter version. Rebuilding in GameMaker is not required.
- **Development style:** Build a small complete playable loop, then add systems in stages.
- **Time model:** One tick represents approximately one local day.
- **Governance domains:** Logistics, Security, Intelligence.
- **Task model:** Agents work on assigned tasks over multiple ticks; task completion should report the outcome and free the agent.
- **Current test action:** `Test Action: Administrative Audit`, a duration-based five-tick task.
- **Dependencies:** Prefer Python standard library until a specific need justifies more.
- **Code layout:** `src/gdsa/` package with Tkinter-free `models.py`/`simulation.py`, `ui.py`, and `app.py`; the project lives at the repository root.
- **Automation default:** The game starts paused with Normal speed selected, so the player can set up before time runs.
- **Tribute notice:** A popup appears on the tick tribute falls due, whether it was paid or not.
- **Resource deficits:** Event losses may drive stock below zero. Tribute is still paid only from available Materials.
- **Coding-agent behavior:** Small changes, tests, diff review, and no unrequested commits/pushes.

## Not yet finalized

- The long-term food and resource economy, including production rates and consumption.
- How population, contentment, security, and ideology interact.
- Exact consequences and cadence for Imperial tribute.
- The final approach to saves and loading.
- Consequences of a resource deficit (currently none beyond the display marker), and whether other costs may draw into deficit.
- Consequences of failing Imperial tribute (currently a log entry and a 7-day grace period).
- Whether and how subordinate needs can be fulfilled. The +2 bonus exists in code but is unreachable; it may be changed.
- Whether hidden AGI is part of the eventual game and how it is revealed.
- When or whether to migrate to a multi-module package; the current direction is gradual extraction once tests protect behavior.
- Distribution/packaging target beyond running the Python application locally.

Do not treat a concept listed in the long-term design as an approved mechanic unless it is promoted into the current milestone with explicit acceptance criteria.
