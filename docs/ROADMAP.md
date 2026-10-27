# Development Roadmap

## Current milestone: Repository foundation and stable prototype

**Goal:** Put the existing playable Python version under version control with a clear, testable development workflow.

- [x] Preserve the working Python/Tkinter version.
- [x] Establish project instructions and documentation.
- [x] Add regression tests for the basic task lifecycle.
- [x] Initialize Git and create the remote repository.
- [ ] Confirm the project launches from the documented path on the development machine.

## Stage A — Operational prototype

**Goal:** The player can assign an agent to an action, advance time, observe progress, and receive a completion report.

- Clock advances one day per tick.
- Agents can be assigned to tasks.
- An agent cannot be assigned to multiple tasks simultaneously.
- Duration-based tasks progress once per tick.
- A five-tick test action completes on the fifth tick, not earlier.
- Completion is logged and the agent becomes available again.
- The GUI continues to launch and display the state correctly.

Current status: the core task behavior is implemented in the single-file prototype. Repository setup and stronger regression coverage remain.

## Stage B — Meaningful administration

**Goal:** Add one resource-linked task that makes an administrative decision matter.

First feature (implemented): `Requisition Food Stores`, a one-time, 5-tick Logistics task that adds 10 Biologics (food) on completion.

Second feature (implemented): `Commission Emergency Food Convoy`, a one-time, 5-tick Logistics task that costs 10 Materials on assignment and adds 20 Biologics on completion. This is the first decision that trades one resource for another.

Neither adds consumption, starvation, persistent bonuses, recurring tasks, or supply chains. Do not implement a complete supply-chain simulation in this stage.

Remaining for Stage B: decide the next food step (repeatable or skill-based production, consumption) and when to retire the Administrative Audit test action.

Entry criteria:
- [x] Stage A tests pass.
- [x] Simulation logic is separated from GUI code enough to test without a display.
- [x] Current resource behavior is documented (`docs/GAME_DESIGN.md`, "Current rules and values").

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
