# Game Design: Grimdark System Admin

## Premise

The player is a feudal space lord responsible for a troubled hive city on an alien world in a decaying interstellar empire. The player governs indirectly through a small group of administrators, strategoi, and courtiers while maintaining the fief, dealing with threats, and meeting Imperial obligations.

The intended experience is one of constrained authority: time passes slowly, actions take time, information is incomplete, and administrative decisions have consequences. As the player's position develops, new actions and information become available.

## Three domains of governance

- **Logistics:** resources, production, infrastructure, and maintenance.
- **Security:** violent threats and their suppression or containment.
- **Intelligence:** morale, information gathering, diplomacy, and relationships.

Subordinates have a dice pool for each domain. Dice pools may combine D3, D6, and D10 dice. In skill-based tasks, the assigned subordinate rolls the relevant pool once per week (every 7 ticks) of work and adds the result to task progress. Most actions are skill-based; a few may be purely time-based. A fulfilled subordinate need currently adds a +2 bonus.

## Time and actions

A simulation tick represents approximately one local day. A tick advances ongoing work, resource generation, Imperial tribute timing, and possible random events. Tasks occupy subordinates while in progress. Completed tasks should be logged and release their assigned subordinate.

## Current implementation

The current Python prototype includes:
- A Tkinter desktop interface with play/pause and speed controls.
- A daily simulation clock.
- Three starting subordinates with generated domain dice pools and needs.
- Task assignment and skill-based task progress (weekly skill rolls).
- A repeatable Logistics food action, `Hydroponics Shift`, that yields Biologics.
- Resource inventories for Materials, Biologics, and Minerals.
- Basic daily resource generation and daily food upkeep.
- Imperial tribute due timing and payment.
- Placeholder random events.
- A duration-based development test action, `Test Action: Administrative Audit`, which completes after five ticks and is used to verify assignment, progress, completion, and agent release.

### Current rules and values

- **Start:** Day 1; Materials 50, Biologics 30, Minerals 20; three subordinates.
- **Tick order:** day advances, tasks progress, resources are generated, tribute is checked, then a random event may occur.
- **Generation per tick (baseline infrastructure):** Materials +1–3, Biologics +1–3, Minerals +0–2.
- **Food:** Food is a sub-type of Biologics and is tracked as Biologics. The hive eats 2 Biologics per tick. Baseline output only barely covers this, so stock slowly erodes under random events. In seeded runs with no player action, about 10% of games reach a Biologics deficit by day 90 and about 45% by day 180.
- **Skill rolls:** an assigned subordinate rolls their domain dice after every 7 ticks of work on a skill-based task, counted from assignment. The Tasks tab shows the days until the next report. Duration-based tasks still advance by 1 each tick.
- **Hydroponics Shift:** Logistics, skill-based, 12 progress, no cost. Completion adds 20 Biologics, and a fresh copy is offered again. It typically takes 3–5 weeks with a D6 agent, 2–3 with a D10 or 2D6, and 5–7 with a D3.
- **Repeatable tasks and rewards:** a task may grant resources on completion and may be repeatable. The other starting tasks are currently one-off and grant nothing.
- **Deficit:** Losses from events and food upkeep can push a stockpile below zero. The UI marks negative stock as a deficit. Generation continues to add normally. A deficit currently has no further consequence (see `DECISIONS.md`).
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

## Design direction: stability and efficiency

Baseline infrastructure provides just barely enough to keep the hive stable. Part of the player's task is finding where to create opportunities by shaking up that stability, at a risk. Through repeated agent actions, investment, and similar means, a district becomes more or less efficient over time.

Actions are skill-based by default, free to undertake for now, and usually repeatable. Setbacks and other scenarios may later require the player to pay resources to complete an action.

Districts and efficiency are not implemented yet.

## Long-term ideas — not current implementation commitments

The broader concept includes population contentment, food production and distribution, upkeep, production chains, security threats, orthodoxy and heresy, Imperial Senate politics, budget and tithe pressures, hidden systems, and a possible hidden AGI/narrative revelation. These belong to later milestones and should not be implemented ahead of the roadmap.

## Tone

The setting is grimdark space feudalism: a vast and decaying empire, oppressive obligations, scarce resources, compromised institutions, and morally uncomfortable administrative trade-offs. The tone should emerge through systems and reports rather than requiring every feature to be elaborate.
