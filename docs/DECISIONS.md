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
- **Resource deficits:** Random events may drive stock below zero. Food upkeep consumes only what is in store and never creates a deficit (changed in issue #11 to avoid an unrecoverable shortage spiral). Voluntary payments (task costs, tribute) are refused instead and never create a deficit.
- **Food (Stage B first step):** The existing Biologics inventory is the city's food supply. The internal resource type and event rules are unchanged.
- **First food action:** `Requisition Food Stores`, a duration-based 5-tick task granting a one-time +10 Biologics on completion. The Administrative Audit test action stays until this loop is verified.
- **Second food action:** `Commission Emergency Food Convoy`, a duration-based 5-tick task. It costs 10 Materials, paid once on successful assignment, never refunded and never driving stock negative, and grants a one-time +20 Biologics on completion.
- **First Security action:** `Restore Order in the Lower Hab-Blocks`, a duration-based 5-tick task costing 5 Materials with no resource reward. Completion grants protection that suppresses exactly the next Food Riots event, then lapses. Implemented as a single task flag (`prevents_next_food_riot`) and a game-state flag (`food_riot_protection`), not a general event-prevention framework.
- **Second Security action (issue #13):** `Maintain District Security Presence`, a repeatable 5-tick task costing 5 Materials. On completion, the next 4 weekly upkeeps compute shortage losses at 90% of the exact value, then round up as before; a loss is never erased, but small losses may be unchanged. It refreshes rather than stacks. Implemented with a `penalty_percent` argument to `feed_groups` (default 100, so the existing rule is unchanged) and a counter, `GameState.security_presence_upkeeps`. This introduced a general `Task.repeatable` flag; only this task uses it.
- **Food upkeep (limited Stage B prototype):** every 7 days, on Day 7, 14, 21, ..., the hive consumes 10 Biologics. It is charged after daily generation and before tribute. A shortfall is logged as a FOOD SHORTAGE; only what is in store is consumed, and the shortfall is not carried as debt. It is a predictable weekly obligation, not per-tick consumption.
- **Population and public order (issue #11):** hidden fixed groups (Nobles 20k, Free Traders 80k, Proles 900k) with demand shares 1/2/7 of the existing upkeep. Contentedness is 0–100 with baselines 70/60/55. Feeding priority is Nobles, then Free Traders, then Proles. Fully fed groups recover +2 per week up to baseline; short groups lose max penalty 8/12/20 times the unmet fraction, rounded up. Public order is the population-weighted average, rounded down: Stable ≥ 50, Strained ≥ 35, Discontented ≥ 20, otherwise Unrest. Only the status is player-facing. The read-only debug tab is enabled with the `--debug` launch flag.
- **Assignment feedback:** rejected assignments show the reason, provided by the simulation (`GameState.assignment_error`).
- **Coding-agent behavior:** Small changes, tests, diff review, and no unrequested commits/pushes.

## Not yet finalized

- The long-term food and resource economy, including production rates and consumption.
- How population, contentment, security, and ideology interact.
- Exact consequences and cadence for Imperial tribute.
- The final approach to saves and loading.
- Whether food actions should become repeatable and/or skill-based, and whether skill rolls should move to a weekly cadence. These were explored in an unmerged proposal (PR #2) and remain excluded. Per-tick food consumption was not adopted; a fixed weekly upkeep is used instead.
- What public order should eventually cause (unrest events, riots, tribute or security effects), and whether food riots or Restore Order should affect contentedness. Currently public order is report-only, and riots and Restore Order do not touch contentedness.
- Whether population should ever change (growth, migration, deaths) and whether upkeep should scale with it. Deferred.
- Food-upkeep balance: baseline output only barely covers upkeep. Values are prototype tuning.
- When to retire the Administrative Audit test action.
- Consequences of a resource deficit (currently none beyond the display marker), and whether other costs may draw into deficit.
- Consequences of failing Imperial tribute (currently a log entry and a 7-day grace period).
- Whether and how subordinate needs can be fulfilled. The +2 bonus exists in code but is unreachable; it may be changed.
- Whether hidden AGI is part of the eventual game and how it is revealed.
- When or whether to migrate to a multi-module package; the current direction is gradual extraction once tests protect behavior.
- Distribution/packaging target beyond running the Python application locally.

Do not treat a concept listed in the long-term design as an approved mechanic unless it is promoted into the current milestone with explicit acceptance criteria.
