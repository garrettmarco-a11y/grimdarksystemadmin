import random
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import call, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.models import (  # noqa: E402
    SKILL_ROLL_INTERVAL_TICKS,
    DicePool,
    DiceType,
    GovernanceArea,
    ResourceType,
    Resources,
    Subordinate,
)
from gdsa.simulation import FOOD_UPKEEP_PER_TICK, GameState, add_starting_tasks  # noqa: E402


def quiet_tick(state):
    """Advance one tick with no random event and no resource generation."""
    with patch("gdsa.simulation.random.random", return_value=1.0):
        with patch("gdsa.simulation.random.randint", return_value=0):
            state.advance_tick()


class SimulationIsolationTests(unittest.TestCase):
    def test_simulation_imports_without_tkinter(self):
        code = (
            "import sys; sys.modules['tkinter'] = None; "
            f"sys.path.insert(0, {str(ROOT / 'src')!r}); "
            "import gdsa.models, gdsa.simulation"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class StartingStateTests(unittest.TestCase):
    def test_new_game_values(self):
        state = GameState()
        self.assertEqual(state.day, 1)
        self.assertEqual(
            (state.resources.materials, state.resources.biologics, state.resources.minerals),
            (50, 30, 20),
        )
        self.assertEqual(
            [s.name for s in state.subordinates],
            ["Administrator Vex", "Strategos Korrath", "Courtier Illyana"],
        )
        self.assertEqual(state.imperial_tribute_due, 7)
        self.assertEqual(state.imperial_tribute_amount, 30)
        self.assertEqual(state.tasks, [])

    def test_starting_subordinate_dice_pools_have_one_or_two_dice(self):
        random.seed(1234)
        for _ in range(50):
            for sub in GameState().subordinates:
                for area in GovernanceArea:
                    self.assertIn(len(sub.get_stat(area).dice), (1, 2))

    def test_starting_tasks(self):
        state = GameState()
        add_starting_tasks(state)
        self.assertEqual(
            [(t.name, t.area, t.required_progress, t.duration_ticks, t.progress, t.assigned_subordinate)
             for t in state.tasks],
            [
                ("Improve Mining Operations", GovernanceArea.LOGISTICS, 15, None, 0, None),
                ("Security Patrol Schedule", GovernanceArea.SECURITY, 12, None, 0, None),
                ("Noble Relations", GovernanceArea.INTELLIGENCE, 20, None, 0, None),
                ("Test Action: Administrative Audit", GovernanceArea.INTELLIGENCE, 5, 5, 0, None),
                ("Hydroponics Shift", GovernanceArea.LOGISTICS, 12, None, 0, None),
            ],
        )
        self.assertEqual(state.tasks[0].description, "Increase mineral extraction efficiency")
        self.assertEqual([t.repeatable for t in state.tasks], [False, False, False, False, True])
        self.assertEqual(state.tasks[4].rewards, {ResourceType.BIOLOGICS: 20})
        self.assertTrue(all(t.rewards == {} for t in state.tasks[:4]))


class DiceTests(unittest.TestCase):
    def test_pool_formatting(self):
        self.assertEqual(str(DicePool([])), "0")
        self.assertEqual(str(DicePool([DiceType.D6])), "D6")
        self.assertEqual(str(DicePool([DiceType.D10, DiceType.D6, DiceType.D6])), "2D6+D10")
        self.assertEqual(str(DicePool([DiceType.D10, DiceType.D3])), "D3+D10")

    def test_roll_stays_within_pool_range(self):
        random.seed(99)
        pool = DicePool([DiceType.D3, DiceType.D10])
        rolls = {pool.roll() for _ in range(500)}
        self.assertEqual(min(rolls), 2)
        self.assertEqual(max(rolls), 13)

    def test_fulfilled_need_adds_two(self):
        agent = Subordinate(
            "Agent", DicePool([DiceType.D6]), DicePool([DiceType.D6]), DicePool([DiceType.D6]),
            need="Rare spices",
        )
        with patch("gdsa.models.random.randint", return_value=3):
            self.assertEqual(agent.roll_for_area(GovernanceArea.SECURITY), 3)
            agent.need_fulfilled = True
            self.assertEqual(agent.roll_for_area(GovernanceArea.SECURITY), 5)


class TaskRuleTests(unittest.TestCase):
    def test_duration_overrides_required_progress(self):
        state = GameState()
        state.add_task("Timed", GovernanceArea.LOGISTICS, required_progress=99, duration_ticks=3)
        self.assertEqual(state.tasks[0].required_progress, 3)

    def test_completion_percentage_is_capped(self):
        state = GameState()
        state.add_task("Task", GovernanceArea.LOGISTICS, required_progress=4)
        state.tasks[0].progress = 2
        self.assertEqual(state.tasks[0].completion_percentage, 50.0)
        state.tasks[0].progress = 8
        self.assertEqual(state.tasks[0].completion_percentage, 100.0)


class SkillTaskTimingTests(unittest.TestCase):
    def make_assigned_task(self, **task_kwargs):
        state = GameState()
        agent = state.subordinates[0]
        state.add_task("Work", GovernanceArea.LOGISTICS, **task_kwargs)
        self.assertTrue(state.assign_subordinate_to_task(agent.name, "Work"))
        return state, agent

    def test_skill_dice_roll_once_per_week_of_work(self):
        self.assertEqual(SKILL_ROLL_INTERVAL_TICKS, 7)
        state, agent = self.make_assigned_task(required_progress=100)
        with patch.object(agent, "roll_for_area", return_value=3) as roll:
            for day in range(1, 15):
                quiet_tick(state)
                self.assertEqual(roll.call_count, day // 7)
        self.assertEqual(state.tasks[0].progress, 6)
        self.assertEqual(
            [e for e in state.events_log if "progress" in e],
            [f"Day 8: {agent.name} made 3 progress on Work", f"Day 15: {agent.name} made 3 progress on Work"],
        )

    def test_days_until_roll_counts_down(self):
        state, _agent = self.make_assigned_task(required_progress=100)
        self.assertEqual(state.tasks[0].days_until_roll, 7)
        for expected in (6, 5, 4, 3, 2, 1, 7):
            quiet_tick(state)
            self.assertEqual(state.tasks[0].days_until_roll, expected)

    def test_unassigned_task_does_not_accumulate_work(self):
        state = GameState()
        state.add_task("Idle", GovernanceArea.LOGISTICS)
        for _ in range(10):
            quiet_tick(state)
        self.assertEqual(state.tasks[0].days_worked, 0)
        self.assertEqual(state.tasks[0].progress, 0)


class TaskCompletionTests(unittest.TestCase):
    def complete(self, state, agent, roll=50):
        with patch.object(agent, "roll_for_area", return_value=roll):
            for _ in range(SKILL_ROLL_INTERVAL_TICKS):
                quiet_tick(state)

    def test_rewards_granted_on_completion(self):
        state = GameState()
        agent = state.subordinates[0]
        state.add_task("Harvest", GovernanceArea.LOGISTICS, 12, rewards={ResourceType.BIOLOGICS: 20})
        state.assign_subordinate_to_task(agent.name, "Harvest")
        self.complete(state, agent)
        upkeep = SKILL_ROLL_INTERVAL_TICKS * FOOD_UPKEEP_PER_TICK
        self.assertEqual(state.resources.biologics, 30 + 20 - upkeep)
        self.assertIn("Day 8: Harvest yields 20 Biologics.", state.events_log)

    def test_repeatable_task_is_offered_again_fresh(self):
        state = GameState()
        agent = state.subordinates[0]
        state.add_task("Harvest", GovernanceArea.LOGISTICS, 12,
                       rewards={ResourceType.BIOLOGICS: 20}, repeatable=True)
        state.assign_subordinate_to_task(agent.name, "Harvest")
        self.complete(state, agent)
        self.assertEqual([t.name for t in state.completed_tasks], ["Harvest"])
        self.assertEqual(len(state.tasks), 1)
        again = state.tasks[0]
        self.assertIsNot(again, state.completed_tasks[0])
        self.assertEqual(
            (again.name, again.progress, again.days_worked, again.assigned_subordinate, again.repeatable),
            ("Harvest", 0, 0, None, True),
        )
        self.assertEqual(again.rewards, {ResourceType.BIOLOGICS: 20})
        self.assertIsNone(agent.current_task)
        self.assertTrue(state.assign_subordinate_to_task(agent.name, "Harvest"))

    def test_non_repeatable_task_is_not_offered_again(self):
        state = GameState()
        agent = state.subordinates[0]
        state.add_task("Once", GovernanceArea.LOGISTICS, 5)
        state.assign_subordinate_to_task(agent.name, "Once")
        self.complete(state, agent)
        self.assertEqual(state.tasks, [])


class ResourceTests(unittest.TestCase):
    def test_add_and_subtract(self):
        resources = Resources()
        resources.add(ResourceType.MINERALS, 5)
        self.assertEqual(resources.minerals, 25)
        self.assertTrue(resources.subtract(ResourceType.MATERIALS, 50))
        self.assertEqual(resources.materials, 0)

    def test_deduct_allows_deficit(self):
        resources = Resources(materials=4)
        resources.deduct(ResourceType.MATERIALS, 10)
        self.assertEqual(resources.materials, -6)
        resources.add(ResourceType.MATERIALS, 2)
        self.assertEqual(resources.materials, -4)

    def test_subtract_refuses_when_insufficient(self):
        resources = Resources(biologics=3)
        self.assertFalse(resources.subtract(ResourceType.BIOLOGICS, 7))
        self.assertEqual(resources.biologics, 3)

    def test_daily_generation_ranges_and_order(self):
        state = GameState()
        with patch("gdsa.simulation.random.random", return_value=1.0):
            with patch("gdsa.simulation.random.randint", return_value=1) as randint:
                state.advance_tick()
        self.assertEqual(randint.call_args_list, [call(1, 3), call(1, 3), call(0, 2)])
        self.assertEqual(
            (state.resources.materials, state.resources.biologics, state.resources.minerals),
            (51, 31 - FOOD_UPKEEP_PER_TICK, 21),
        )

    def test_hive_eats_biologics_each_tick(self):
        self.assertEqual(FOOD_UPKEEP_PER_TICK, 2)
        state = GameState()
        quiet_tick(state)
        self.assertEqual(state.resources.biologics, 28)

    def test_food_upkeep_can_push_biologics_into_deficit(self):
        state = GameState()
        state.resources.biologics = 1
        quiet_tick(state)
        self.assertEqual(state.resources.biologics, -1)


class TributeTests(unittest.TestCase):
    def test_tribute_not_collected_before_due(self):
        state = GameState()
        state.imperial_tribute_due = 2
        quiet_tick(state)
        self.assertEqual(state.imperial_tribute_due, 1)
        self.assertEqual(state.resources.materials, 50)
        self.assertEqual(state.events_log, [])

    def test_first_tribute_falls_due_on_day_eight(self):
        state = GameState()
        for _ in range(7):
            quiet_tick(state)
        self.assertEqual(state.day, 8)
        self.assertEqual(state.resources.materials, 20)
        self.assertIn("Day 8: Imperial tribute of 30 Materials paid.", state.events_log)

    def test_paid_tribute_resets_to_thirty_days(self):
        state = GameState()
        state.imperial_tribute_due = 1
        quiet_tick(state)
        self.assertEqual(state.resources.materials, 20)
        self.assertEqual(state.imperial_tribute_due, 30)

    def test_failed_tribute_grants_seven_day_grace_and_keeps_materials(self):
        state = GameState()
        state.resources.materials = 29
        state.imperial_tribute_due = 1
        quiet_tick(state)
        self.assertEqual(state.resources.materials, 29)
        self.assertEqual(state.imperial_tribute_due, 7)
        self.assertTrue(any("Failed to pay Imperial tribute" in e for e in state.events_log))

    def test_tribute_cannot_be_paid_from_deficit(self):
        state = GameState()
        state.resources.materials = -5
        state.imperial_tribute_due = 1
        quiet_tick(state)
        self.assertEqual(state.resources.materials, -5)
        self.assertEqual(state.tribute_outcome, "failed")

    def test_tribute_outcome_reported_only_on_due_tick(self):
        state = GameState()
        self.assertIsNone(state.tribute_outcome)
        state.imperial_tribute_due = 2
        quiet_tick(state)
        self.assertIsNone(state.tribute_outcome)
        quiet_tick(state)
        self.assertEqual(state.tribute_outcome, "paid")
        quiet_tick(state)
        self.assertIsNone(state.tribute_outcome)

    def test_tribute_outcome_failed(self):
        state = GameState()
        state.resources.materials = 0
        state.imperial_tribute_due = 1
        quiet_tick(state)
        self.assertEqual(state.tribute_outcome, "failed")


class RandomEventTests(unittest.TestCase):
    def run_event(self, state, event_text, amount):
        with patch("gdsa.simulation.random.choice", return_value=event_text):
            with patch("gdsa.simulation.random.randint", return_value=amount):
                state._generate_random_event()

    def test_event_chance_is_ten_percent(self):
        state = GameState()
        with patch.object(state, "_generate_random_event") as event:
            with patch("gdsa.simulation.random.random", return_value=0.0999):
                state.advance_tick()
            with patch("gdsa.simulation.random.random", return_value=0.1):
                state.advance_tick()
        self.assertEqual(event.call_count, 1)

    def test_mining_event_adds_minerals(self):
        state = GameState()
        self.run_event(state, "Asteroid mining yields extra minerals!", 5)
        self.assertEqual(state.resources.minerals, 25)
        self.assertEqual(state.events_log, ["Day 1: Asteroid mining yields extra minerals!"])

    def test_riot_event_consumes_biologics(self):
        state = GameState()
        self.run_event(state, "Food riots in the lower sectors - biologics consumed.", 7)
        self.assertEqual(state.resources.biologics, 23)

    def test_malfunction_event_consumes_materials(self):
        state = GameState()
        self.run_event(state, "Equipment malfunction - materials needed for repairs.", 4)
        self.assertEqual(state.resources.materials, 46)

    def test_riot_event_can_push_biologics_into_deficit(self):
        state = GameState()
        state.resources.biologics = 3
        self.run_event(state, "Food riots in the lower sectors - biologics consumed.", 7)
        self.assertEqual(state.resources.biologics, -4)

    def test_malfunction_event_can_push_materials_into_deficit(self):
        state = GameState()
        state.resources.materials = 2
        self.run_event(state, "Equipment malfunction - materials needed for repairs.", 5)
        self.assertEqual(state.resources.materials, -3)

    def test_flavor_events_change_no_resources(self):
        for text in (
            "Merchant convoy arrives with trade opportunities.",
            "Heretic cell discovered in the manufacturing district.",
        ):
            state = GameState()
            self.run_event(state, text, 5)
            self.assertEqual(
                (state.resources.materials, state.resources.biologics, state.resources.minerals),
                (50, 30, 20),
            )


if __name__ == "__main__":
    unittest.main()
