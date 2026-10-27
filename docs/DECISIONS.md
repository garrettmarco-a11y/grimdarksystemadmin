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
- **Food (Stage B first step):** The existing Biologics inventory is the city's food supply. The internal resource type and event rules are unchanged.
- **First food action:** `Requisition Food Stores`, a duration-based 5-tick task granting a one-time +10 Biologics on completion. The Administrative Audit test action stays until this loop is verified.
- **Second food action:** `Commission Emergency Food Convoy`, a duration-based 5-tick task. It costs 10 Materials, paid once on successful assignment, never refunded and never driving stock negative, and grants a one-time +20 Biologics on completion.
- **First Security action:** `Restore Order in the Lower Hab-Blocks`, a duration-based 5-tick task costing 5 Materials with no resource reward. Completion grants protection that suppresses exactly the next Food Riots event, then lapses. Implemented as a single task flag (`prevents_next_food_riot`) and a game-state flag (`food_riot_protection`), not a general event-prevention framework.
- **Assignment feedback:** rejected assignments show the reason, provided by the simulation (`GameState.assignment_error`).
- **Coding-agent behavior:** Small changes, tests, diff review, and no unrequested commits/pushes.

## Not yet finalized

- The long-term food and resource economy, including production rates and consumption.
- How population, contentment, security, and ideology interact.
- Exact consequences and cadence for Imperial tribute.
- The final approach to saves and loading.
- Whether food actions should become repeatable and/or skill-based, whether skill rolls should move to a weekly cadence, and whether the hive should consume food each tick. These were explored in an unmerged proposal (PR #2) and are deliberately excluded from this step.
- When to retire the Administrative Audit test action.
- Consequences of a resource deficit (currently none beyond the display marker), and whether other costs may draw into deficit.
- Consequences of failing Imperial tribute (currently a log entry and a 7-day grace period).
- Whether and how subordinate needs can be fulfilled. The +2 bonus exists in code but is unreachable; it may be changed.
- Whether hidden AGI is part of the eventual game and how it is revealed.
- When or whether to migrate to a multi-module package; the current direction is gradual extraction once tests protect behavior.
- Distribution/packaging target beyond running the Python application locally.

Do not treat a concept listed in the long-term design as an approved mechanic unless it is promoted into the current milestone with explicit acceptance criteria.
