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
