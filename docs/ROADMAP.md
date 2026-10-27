# Development Roadmap

## Current milestone: Stage B — Meaningful administration

**Goal:** Add a small set of resource-linked actions that make administrative choices matter, while keeping the game playable and avoiding a premature full-economy simulation.

### Stage A — Operational prototype

**Goal:** The player can assign an agent to an action, advance time, observe progress, and receive a completion report.

- [x] Clock advances one day per tick.
- [x] Agents can be assigned to tasks.
- [x] An agent cannot be assigned to multiple tasks simultaneously.
- [x] Duration-based tasks progress once per tick.
- [x] A five-tick test action completes on the fifth tick, not earlier.
- [x] Completion is logged and the agent becomes available again.
- [x] Simulation logic is separated from GUI code enough to test without a display.
- [ ] Confirm the project launches and behaves correctly on the developer's physical desktop after recent changes.

Stage A's core task loop is implemented and covered by tests. The remaining checkbox is a manual verification reminder, not a blocker for reviewing the simulation rules.

### Stage B — Meaningful administration

Implemented starting actions:

1. **Requisition Food Stores** — Logistics, one-time, five ticks, no cost, +10 Biologics on completion.
2. **Commission Emergency Food Convoy** — Logistics, one-time, five ticks, costs 10 Materials on assignment, +20 Biologics on completion.
3. **Restore Order in the Lower Hab-Blocks** — Security, one-time, five ticks, costs 5 Materials on assignment, suppresses the next Food Riots event after completion.

These actions introduce a basic reward, a resource trade, and a preventive action. Costs are paid on successful assignment; rewards and protection activate on completion. The Administrative Audit test action remains available.

**Food upkeep (implemented, limited prototype):** every 7 days (Day 7, 14, 21, ...) the hive consumes 10 Biologics. A shortfall is logged as a FOOD SHORTAGE and leaves Biologics in deficit, with no further consequence. This gives the player a predictable obligation to plan around, which random events can complicate.

**Current boundary:** There is no per-tick consumption, starvation, population or contentment effect, recurring production, or full supply-chain simulation. Daily resource generation, tribute, and placeholder random events remain as previously documented. Do not add those systems by implication.

**Next step — design decision, not an approved implementation task:** Decide what the next playable loop should demonstrate before adding another mechanic. In particular:
- Food now has a weekly upkeep but only one-off replenishment actions. Should the next milestone introduce recurring production?
- What player-visible consequence should a food shortfall have beyond the current shortage report and deficit marker?
- When can the Administrative Audit test action be retired without losing useful regression coverage?

The older proposal in PR #2 combines weekly skill rolls, upkeep, and repeatable Hydroponics Shift. It is not approved for the current direction and should not be merged as-is. Any of those ideas should be reconsidered separately with explicit acceptance criteria.

Entry criteria:
- [x] Stage A tests pass.
- [x] Simulation logic is separated from GUI code enough to test without a display.
- [x] Current resource behavior is documented in `docs/GAME_DESIGN.md`.

## Stage C — Interconnected pressures

Potential systems:
- Population contentment.
- Security threat or instability.
- A recurring financial or Imperial obligation.
- Consequences that connect resources and agent actions.

Only add a system when the player can understand its inputs, consequences, and feedback.

## Stage D — Institutions and ideology

Potential systems:
- Orthodoxy and heresy.
- Imperial Senate or noble political relationships.
- More nuanced tribute/budget and political pressures.

These are later features, not requirements for the current prototype.

## Stage E — Hidden systems and narrative revelations

Potential features include hidden information, concealed systemic causes, and a possible AGI-related revelation. Keep these out of scope until the core administrative loop supports them.

## Milestone policy

Each milestone should have:
- A short player-visible goal.
- A bounded implementation scope.
- Acceptance criteria.
- Tests for the underlying rules.
- A playable build at the end.

Do not begin the next milestone just because its features are described here. Confirm the current milestone is stable first.
