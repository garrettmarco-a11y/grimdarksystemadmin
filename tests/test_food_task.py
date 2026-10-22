import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.models import GovernanceArea, ResourceType  # noqa: E402
from gdsa.simulation import GameState, add_starting_tasks  # noqa: E402

FOOD_TASK = "Requisition Food Stores"


def quiet_tick(state):
    """Advance one tick with no random event and no resource generation."""
    with patch("gdsa.simulation.random.random", return_value=1.0):
        with patch("gdsa.simulation.random.randint", return_value=0):
            state.advance_tick()


class FoodTaskTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        add_starting_tasks(self.state)
        self.agent = self.state.subordinates[0]

    def food_task(self):
        return next(t for t in self.state.tasks if t.name == FOOD_TASK)

    def test_available_at_start_with_description_and_reward(self):
        task = self.food_task()
        self.assertEqual(task.area, GovernanceArea.LOGISTICS)
        self.assertEqual((task.duration_ticks, task.required_progress, task.progress), (5, 5, 0))
        self.assertEqual(task.rewards, {ResourceType.BIOLOGICS: 10})
        self.assertIn("10 Biologics", task.description)
        self.assertIn("food", task.description)
        self.assertIsNone(task.assigned_subordinate)

    def test_audit_test_action_still_available(self):
        self.assertIn("Test Action: Administrative Audit", [t.name for t in self.state.tasks])

    def test_assignment_and_busy_subordinate_rejected(self):
        self.assertTrue(self.state.assign_subordinate_to_task(self.agent.name, FOOD_TASK))
        self.assertEqual(self.agent.current_task, FOOD_TASK)
        self.assertEqual(self.food_task().assigned_subordinate, self.agent.name)
        self.assertFalse(self.state.assign_subordinate_to_task(self.agent.name, "Noble Relations"))
        self.assertEqual(self.agent.current_task, FOOD_TASK)

    def test_progress_one_per_tick_with_no_early_reward(self):
        self.state.assign_subordinate_to_task(self.agent.name, FOOD_TASK)
        for expected in range(1, 5):
            quiet_tick(self.state)
            self.assertEqual(self.food_task().progress, expected)
            self.assertEqual(self.state.resources.biologics, 30)
            self.assertEqual(self.agent.current_task, FOOD_TASK)
        self.assertEqual(self.state.completed_tasks, [])

    def test_completes_on_fifth_tick_with_reward_and_release(self):
        self.state.assign_subordinate_to_task(self.agent.name, FOOD_TASK)
        for _ in range(5):
            quiet_tick(self.state)
        self.assertEqual(self.state.resources.biologics, 40)
        self.assertEqual([t.name for t in self.state.completed_tasks], [FOOD_TASK])
        self.assertNotIn(FOOD_TASK, [t.name for t in self.state.tasks])
        self.assertIsNone(self.agent.current_task)
        self.assertIsNone(self.state.completed_tasks[0].assigned_subordinate)
        self.assertIn(f"Day 6: Task '{FOOD_TASK}' completed!", self.state.events_log)
        self.assertIn(
            f"Day 6: {FOOD_TASK} delivers 10 Biologics to the hive's stores.", self.state.events_log
        )

    def test_reward_granted_exactly_once(self):
        self.state.assign_subordinate_to_task(self.agent.name, FOOD_TASK)
        for _ in range(5):
            quiet_tick(self.state)
        for _ in range(10):
            quiet_tick(self.state)
        self.assertEqual(self.state.resources.biologics, 40)
        self.assertEqual(sum("delivers" in e for e in self.state.events_log), 1)
        self.assertFalse(self.state.assign_subordinate_to_task(self.agent.name, FOOD_TASK))

    def test_released_subordinate_can_take_new_task(self):
        self.state.assign_subordinate_to_task(self.agent.name, FOOD_TASK)
        for _ in range(5):
            quiet_tick(self.state)
        self.assertTrue(self.state.assign_subordinate_to_task(self.agent.name, "Noble Relations"))

    def test_reward_adds_on_top_of_normal_generation(self):
        self.state.assign_subordinate_to_task(self.agent.name, FOOD_TASK)
        with patch("gdsa.simulation.random.random", return_value=1.0):
            with patch("gdsa.simulation.random.randint", return_value=1):
                for _ in range(5):
                    self.state.advance_tick()
        self.assertEqual(self.state.resources.biologics, 30 + 5 + 10)

    def test_tasks_without_rewards_grant_nothing(self):
        state = GameState()
        agent = state.subordinates[0]
        state.add_task("Plain", GovernanceArea.LOGISTICS, duration_ticks=2)
        state.assign_subordinate_to_task(agent.name, "Plain")
        for _ in range(2):
            quiet_tick(state)
        self.assertEqual(
            (state.resources.materials, state.resources.biologics, state.resources.minerals),
            (50, 30, 20),
        )


if __name__ == "__main__":
    unittest.main()
