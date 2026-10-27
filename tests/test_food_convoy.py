import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.models import GovernanceArea, ResourceType  # noqa: E402
from gdsa.simulation import FOOD_UPKEEP_AMOUNT, GameState, add_starting_tasks  # noqa: E402

CONVOY = "Commission Emergency Food Convoy"


def quiet_tick(state):
    """Advance one tick with no random event and no resource generation."""
    with patch("gdsa.simulation.random.random", return_value=1.0):
        with patch("gdsa.simulation.random.randint", return_value=0):
            state.advance_tick()


def stock(state):
    r = state.resources
    return (r.materials, r.biologics, r.minerals)


class FoodConvoyTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        add_starting_tasks(self.state)
        self.agent = self.state.subordinates[0]
        self.other = self.state.subordinates[1]

    def convoy(self):
        return next(t for t in self.state.tasks if t.name == CONVOY)

    def assign(self, agent=None):
        return self.state.assign_subordinate_to_task((agent or self.agent).name, CONVOY)

    # Availability

    def test_available_at_start_with_clear_description(self):
        task = self.convoy()
        self.assertEqual(task.area, GovernanceArea.LOGISTICS)
        self.assertEqual((task.duration_ticks, task.required_progress, task.progress), (5, 5, 0))
        self.assertEqual(task.cost, {ResourceType.MATERIALS: 10})
        self.assertEqual(task.rewards, {ResourceType.BIOLOGICS: 20})
        self.assertIsNone(task.assigned_subordinate)
        for phrase in ("10 Materials", "5 days", "20 Biologics"):
            self.assertIn(phrase, task.description)

    def test_other_food_task_and_audit_remain_available(self):
        names = [t.name for t in self.state.tasks]
        self.assertIn("Requisition Food Stores", names)
        self.assertIn("Test Action: Administrative Audit", names)

    # Cost on assignment

    def test_successful_assignment_deducts_ten_materials_once(self):
        self.assertIsNone(self.state.assignment_error(self.agent.name, CONVOY))
        self.assertTrue(self.assign())
        self.assertEqual(stock(self.state), (40, 30, 20))
        self.assertEqual(self.agent.current_task, CONVOY)
        self.assertEqual(self.convoy().assigned_subordinate, self.agent.name)
        self.assertIn(
            f"Day 1: {self.agent.name} assigned to {CONVOY}; 10 Materials spent.", self.state.events_log
        )

    def test_repeating_same_assignment_does_not_charge_again(self):
        self.assertTrue(self.assign())
        self.assertTrue(self.assign())
        self.assertEqual(self.state.resources.materials, 40)
        self.assertEqual(sum("spent" in e for e in self.state.events_log), 1)

    def test_exactly_ten_materials_is_enough(self):
        self.state.resources.materials = 10
        self.assertTrue(self.assign())
        self.assertEqual(self.state.resources.materials, 0)

    def test_insufficient_materials_rejected_without_state_change(self):
        self.state.resources.materials = 9
        self.assertEqual(
            self.state.assignment_error(self.agent.name, CONVOY),
            f"Not enough Materials: {CONVOY} costs 10 Materials, but only 9 are available.",
        )
        self.assertFalse(self.assign())
        self.assertEqual(stock(self.state), (9, 30, 20))
        self.assertIsNone(self.agent.current_task)
        self.assertIsNone(self.convoy().assigned_subordinate)
        self.assertEqual(self.state.events_log, [])

    def test_deficit_materials_rejected_and_not_driven_further_negative(self):
        self.state.resources.materials = -3
        self.assertFalse(self.assign())
        self.assertEqual(self.state.resources.materials, -3)
        self.assertIn("only -3 are available", self.state.assignment_error(self.agent.name, CONVOY))

    def test_busy_subordinate_rejected_without_charge(self):
        self.assertTrue(self.state.assign_subordinate_to_task(self.agent.name, "Requisition Food Stores"))
        self.assertEqual(
            self.state.assignment_error(self.agent.name, CONVOY),
            f"{self.agent.name} is already working on Requisition Food Stores.",
        )
        self.assertFalse(self.assign())
        self.assertEqual(stock(self.state), (50, 30, 20))
        self.assertIsNone(self.convoy().assigned_subordinate)

    def test_assigned_convoy_rejects_second_subordinate_without_charge(self):
        self.assertTrue(self.assign())
        self.assertEqual(
            self.state.assignment_error(self.other.name, CONVOY),
            f"{CONVOY} is already assigned to {self.agent.name}.",
        )
        self.assertFalse(self.assign(self.other))
        self.assertEqual(self.state.resources.materials, 40)
        self.assertIsNone(self.other.current_task)

    def test_convoy_subordinate_cannot_take_another_task(self):
        self.assertTrue(self.assign())
        self.assertFalse(self.state.assign_subordinate_to_task(self.agent.name, "Requisition Food Stores"))
        self.assertEqual(self.agent.current_task, CONVOY)

    # Timing and reward

    def test_progress_one_per_tick_no_early_reward(self):
        self.assign()
        for expected in range(1, 5):
            quiet_tick(self.state)
            self.assertEqual(self.convoy().progress, expected)
            self.assertEqual(stock(self.state), (40, 30, 20))
            self.assertEqual(self.agent.current_task, CONVOY)
        self.assertEqual(self.state.completed_tasks, [])

    def test_completes_on_fifth_tick_with_reward_and_release(self):
        self.assign()
        for _ in range(5):
            quiet_tick(self.state)
        self.assertEqual(stock(self.state), (40, 50, 20))
        self.assertEqual([t.name for t in self.state.completed_tasks], [CONVOY])
        self.assertNotIn(CONVOY, [t.name for t in self.state.tasks])
        self.assertIsNone(self.agent.current_task)
        self.assertIn(f"Day 6: Task '{CONVOY}' completed!", self.state.events_log)
        self.assertIn(f"Day 6: {CONVOY} delivers 20 Biologics to the hive's stores.", self.state.events_log)

    def test_reward_granted_once_and_task_cannot_be_reassigned(self):
        self.state.imperial_tribute_due = 100  # Keep tribute out of this resource check
        self.assign()
        for _ in range(15):
            quiet_tick(self.state)
        # Days 7 and 14 each charge food upkeep.
        self.assertEqual(stock(self.state), (40, 50 - 2 * FOOD_UPKEEP_AMOUNT, 20))
        self.assertEqual(sum("delivers 20" in e for e in self.state.events_log), 1)
        self.assertEqual(
            self.state.assignment_error(self.agent.name, CONVOY), f"No available task named '{CONVOY}'."
        )
        self.assertFalse(self.assign())
        self.assertEqual(self.state.resources.materials, 40)

    def test_released_subordinate_can_take_new_task(self):
        self.assign()
        for _ in range(5):
            quiet_tick(self.state)
        self.assertTrue(self.state.assign_subordinate_to_task(self.agent.name, "Noble Relations"))

    def test_daily_generation_continues_alongside_cost_and_reward(self):
        self.assign()
        with patch("gdsa.simulation.random.random", return_value=1.0):
            with patch("gdsa.simulation.random.randint", return_value=1):
                for _ in range(5):
                    self.state.advance_tick()
        # Generation adds 1 of each per tick under the patch: 5 ticks.
        self.assertEqual(stock(self.state), (50 - 10 + 5, 30 + 5 + 20, 20 + 5))

    def test_tasks_without_cost_are_free_and_unlogged_on_assignment(self):
        self.assertTrue(self.state.assign_subordinate_to_task(self.agent.name, "Requisition Food Stores"))
        self.assertEqual(stock(self.state), (50, 30, 20))
        self.assertEqual(self.state.events_log, [])

    # Error messages for other rejections

    def test_unknown_subordinate_and_task_explained(self):
        self.assertEqual(self.state.assignment_error("Nobody", CONVOY), "No subordinate named 'Nobody'.")
        self.assertEqual(
            self.state.assignment_error(self.agent.name, "Nothing"), "No available task named 'Nothing'."
        )


if __name__ == "__main__":
    unittest.main()
