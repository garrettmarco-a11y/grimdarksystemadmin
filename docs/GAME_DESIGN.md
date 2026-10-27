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
- Imperial tribute due timing and payment.
- Placeholder random events.
- A duration-based development test action, `Test Action: Administrative Audit`, which completes after five ticks and is used to verify assignment, progress, completion, and agent release.
- A one-time food production action, `Requisition Food Stores`, which completes after five ticks and adds 10 Biologics.
- A one-time, resource-cost food action, `Commission Emergency Food Convoy`, which costs 10 Materials on assignment, completes after five ticks and adds 20 Biologics.

### Current rules and values

- **Start:** Day 1; Materials 50, Biologics 30, Minerals 20; three subordinates.
- **Food:** Biologics serve as the hive's food supply. The UI labels them "Biologics (food)". There is no food consumption yet.
- **Task rewards:** a task may grant resources once, on the tick it completes. No partial rewards are given, and a completed task leaves the task list, so it cannot pay out again.
- **Task costs:** a task may cost resources, paid once when a subordinate is successfully assigned. If any stock is below the cost, the assignment is rejected with an explanation (e.g. "Not enough Materials: … costs 10 Materials, but only 7 are available."). Nothing is charged, and no task or subordinate state changes. A cost never drives a stockpile negative. Rejections for a busy subordinate or an already-assigned task are also explained and never charge. Re-confirming the same subordinate on the same task does not charge again. A paid cost is not refunded; there is no cancellation. A costed assignment is logged as "<subordinate> assigned to <task>; 10 Materials spent." Free tasks are not logged on assignment, as before.
- **Requisition Food Stores:** Logistics, duration-based, 5 ticks (one progress per tick, completes on tick five), no cost, one-time, +10 Biologics on completion. It is logged as "<task> delivers 10 Biologics to the hive's stores." The reward is added in the task step of the tick, before normal generation.
- **Commission Emergency Food Convoy:** Logistics, duration-based, 5 ticks, one-time. It costs 10 Materials on assignment and adds +20 Biologics on completion, logged the same way. The subordinate stays busy until completion and is then released. It is a bounded trade: spend Materials now and tie up one subordinate for five days in exchange for a larger food delivery. Values are prototype tuning, not final balance.
- **Tick order:** day advances, tasks progress, resources are generated, tribute is checked, then a random event may occur.
- **Generation per tick:** Materials +1–3, Biologics +1–2, Minerals +0–2.
- **Deficit:** Losses from events can push a stockpile below zero. The UI marks negative stock as a deficit. Generation continues to add normally. A deficit currently has no further consequence (see `DECISIONS.md`).
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
