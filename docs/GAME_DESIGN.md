# Game Design: Grimdark System Admin

## Premise

The player is a feudal space lord responsible for a troubled hive city on an alien world in a decaying interstellar empire. The player governs indirectly through a small group of administrators, strategoi, and courtiers while maintaining the fief, dealing with threats, and meeting Imperial obligations.

The intended experience is one of constrained authority: time passes slowly, actions take time, information is incomplete, and administrative decisions have consequences. As the player's position develops, new actions and information become available.

## Three domains of governance

- **Logistics:** resources, production, infrastructure, and maintenance.
- **Security:** violent threats and their suppression or containment.
- **Intelligence:** morale, information gathering, diplomacy, and relationships.

Subordinates have a dice pool for each domain. Dice pools may combine D3, D6, and D10 dice. In skill-based tasks, the assigned subordinate rolls the relevant pool each tick and adds the result to task progress. A fulfilled subordinate need currently adds a +2 bonus.

## Time and actions

A simulation tick represents approximately one local day. A tick advances ongoing work, resource generation, Imperial tribute timing, and possible random events. Tasks occupy subordinates while in progress. Completed tasks should be logged and release their assigned subordinate.

## Current implementation

The current Python prototype includes:
- A Tkinter desktop interface with play/pause and speed controls.
- A daily simulation clock.
- Three starting subordinates with generated domain dice pools and needs.
- Task assignment and skill-based task progress.
- Resource inventories for Materials, Biologics, and Minerals.
- Basic daily resource generation.
- A limited food upkeep: 10 Biologics consumed every 7 days, starting on Day 7.
- Hidden population groups (Proles, Free Traders, Nobles) whose contentedness responds to food upkeep, shown to the player only as a broad public-order status.
- Imperial tribute due timing and payment.
- Placeholder random events.
- A duration-based development test action, `Test Action: Administrative Audit`, which completes after five ticks and is used to verify assignment, progress, completion, and agent release.
- A one-time food production action, `Requisition Food Stores`, which completes after five ticks and adds 10 Biologics.
- A one-time, resource-cost food action, `Commission Emergency Food Convoy`, which costs 10 Materials on assignment, completes after five ticks and adds 20 Biologics.
- A one-time Security action, `Restore Order in the Lower Hab-Blocks`, which costs 5 Materials on assignment, completes after five ticks and prevents the next Food Riots event.

### Current rules and values

- **Start:** Day 1; Materials 50, Biologics 30, Minerals 20; three subordinates.
- **Food:** Biologics serve as the hive's food supply. The UI labels them "Biologics (food)".
- **Food upkeep (limited Stage B prototype):** on every day divisible by 7 (Day 7, 14, 21, ...) the hive consumes 10 Biologics. It is resolved once in that day's tick, after daily generation and before the tribute check, and uses no randomness. A sufficient stockpile logs "Food upkeep: the hive consumes 10 Biologics." If fewer than 10 are in store, upkeep consumes only what is there (never below 0) and the shortfall is not carried as debt. It is logged as "FOOD SHORTAGE: upkeep needed 10 Biologics but only N were in store. The hive went S short." If random events have already left Biologics negative, upkeep consumes nothing and does not deepen the deficit. The food actually consumed feeds the population groups (below). The status bar shows "Food Upkeep Due: N days (10 Biologics)", marked ⚠️ when current Biologics are below 10. These are prototype values, not final balance.
- **Population groups (hidden):** three fixed groups whose population never changes yet. Each has a share of the weekly 10-Biologics upkeep, so total demand is exactly the existing upkeep. Contentedness is a whole number from 0 to 100; each group starts at its baseline.

  | Group | Population (thousands) | Share of upkeep | Baseline / start | Max weekly shortage penalty |
  |---|---|---|---|---|
  | Nobles | 20 | 1 | 70 | 8 |
  | Free Traders | 80 | 2 | 60 | 12 |
  | Proles | 900 | 7 | 55 | 20 |

- **Weekly contentedness rule:** at each upkeep, the Biologics consumed feed the groups in priority order: Nobles, then Free Traders, then Proles. A fully fed group gains +2, but never above its baseline; a group already above its baseline is left alone. A group that gets less than its share loses its max penalty times the unmet fraction, rounded up (e.g. Proles fed 2 of 7 lose ⌈5/7 × 20⌉ = 15), with a floor of 0. Shortages therefore hit Proles first and hardest. There are no deaths, starvation, migration, or population change.
- **Public order (player-facing):** the population-weighted average contentedness, rounded down, maps to a status: ≥ 50 Stable, 35–49 Strained, 20–34 Discontented, < 20 Unrest. A new game starts at 55 (Stable). For example, one week with 5 Biologics in store makes it Strained, and three consecutive weeks with none make it Unrest. The status bar shows "Public Order: <status>" (⚠️ unless Stable), and the event log records "Public order in the hive is now <status>." only when the status changes. Group names, populations, and contentedness never appear in the normal interface or the event log.
- **Debug view:** launching with `--debug` adds a read-only tab, "DEBUG: Population". It shows each group's population, demand share, contentedness, baseline and max penalty; the weighted value, status and thresholds; and the most recent upkeep (Biologics in store, food each group received, before → after). It is produced by `GameState.population_debug_report()`, which does not modify state.
- **Task rewards:** a task may grant resources once, on the tick it completes. No partial rewards are given, and a completed task leaves the task list, so it cannot pay out again.
- **Task costs:** a task may cost resources, paid once when a subordinate is successfully assigned. If any stock is below the cost, the assignment is rejected with an explanation (e.g. "Not enough Materials: … costs 10 Materials, but only 7 are available."). Nothing is charged, and no task or subordinate state changes. A cost never drives a stockpile negative. Rejections for a busy subordinate or an already-assigned task are also explained and never charge. Re-confirming the same subordinate on the same task does not charge again. A paid cost is not refunded; there is no cancellation. A costed assignment is logged as "<subordinate> assigned to <task>; 10 Materials spent." Free tasks are not logged on assignment, as before.
- **Requisition Food Stores:** Logistics, duration-based, 5 ticks (one progress per tick, completes on tick five), no cost, one-time, +10 Biologics on completion. It is logged as "<task> delivers 10 Biologics to the hive's stores." The reward is added in the task step of the tick, before normal generation.
- **Commission Emergency Food Convoy:** Logistics, duration-based, 5 ticks, one-time. It costs 10 Materials on assignment and adds +20 Biologics on completion, logged the same way. The subordinate stays busy until completion and is then released. It is a bounded trade: spend Materials now and tie up one subordinate for five days in exchange for a larger food delivery. Values are prototype tuning, not final balance.
- **Restore Order in the Lower Hab-Blocks:** Security, duration-based, 5 ticks, one-time. It costs 5 Materials on assignment and grants no resource reward. On completion it activates riot protection, logged as "Order holds in the lower hab-blocks. The next food riot will be suppressed." While protection is active, the next Food Riots event selected by the random-event roll is suppressed instead of occurring. No Biologics are lost, it is logged as "Food riots threatened the lower sectors, but Security forces suppressed them. No biologics lost; the protection is spent.", and the protection is consumed. Protection does not exist before completion, lasts indefinitely until it suppresses a riot, does not stack (it is a single flag), and never affects other events. Event probability and selection are unchanged. A riot that occurs while the task is still in progress is not prevented. This is a bounded trade: spend Materials and a subordinate's time now to avoid a possible food loss later.
- **Tick order:** day advances, tasks progress, resources are generated, food upkeep is charged (on upkeep days), tribute is checked, then a random event may occur.
- **Generation per tick:** Materials +1–3, Biologics +1–2, Minerals +0–2.
- **Deficit:** Random events can push a stockpile below zero; food upkeep and voluntary payments (task costs, tribute) never do. The UI marks negative stock as a deficit. Generation continues to add normally. A deficit currently has no further consequence (see `DECISIONS.md`).
- **Tribute:** 30 Materials, first due on day 8, then every 30 days after payment. It is paid only if Materials ≥ 30; tribute never creates a deficit. Failing logs a warning and sets a 7-day grace period, with no other consequence yet. On the tick tribute falls due, the GUI shows a popup: confirmation if paid, warning if not.
- **Random events:** 10% chance per tick of one of five placeholder events. Asteroid mining +3–8 Minerals; food riots −5–10 Biologics; equipment malfunction −3–7 Materials; merchant convoy and heretic cell are log-only.
- **Need bonus:** a subordinate with `need_fulfilled` adds +2 to rolls, but no current action fulfils needs, so the bonus is unreachable in play.
- **Automation:** the game starts paused with Normal speed selected; Play runs at the selected speed (Slow 2s, Normal 1s, Fast 0.5s per tick).

The current implementation is a prototype, not a complete or balanced game. Current values and random events should not automatically be treated as final design decisions.

## Design principles

1. **Small playable loop first.** Maintain a complete, runnable game while developing.
2. **Actions over menus of disconnected systems.** New systems should connect to time, agents, resources, information, or consequences.
3. **Indirect rule.** The player acts through agents, with limited capacity and incomplete information.
4. **Progressive revelation.** New systems and information should be introduced through milestones rather than exposing every system at the start.
5. **Testable simulation.** Core rules should eventually be testable without launching the GUI.
6. **Explicit uncertainty.** Separate established behavior from proposed ideas and unresolved design choices.

## Long-term ideas — not current implementation commitments

The broader concept includes population contentment, food production and distribution, upkeep, production chains, security threats, orthodoxy and heresy, Imperial Senate politics, budget and tithe pressures, hidden systems, and a possible hidden AGI/narrative revelation. These belong to later milestones and should not be implemented ahead of the roadmap.

## Tone

The setting is grimdark space feudalism: a vast and decaying empire, oppressive obligations, scarce resources, compromised institutions, and morally uncomfortable administrative trade-offs. The tone should emerge through systems and reports rather than requiring every feature to be elaborate.
