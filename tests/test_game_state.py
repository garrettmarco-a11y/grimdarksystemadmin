import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.models import DicePool, DiceType, GovernanceArea, Subordinate  # noqa: E402
from gdsa.simulation import GameState  # noqa: E402


class GameStateTaskTests(unittest.TestCase):
    def make_state_with_one_agent(self):
        state = GameState()
        agent = Subordinate(
            name="Test Administrator",
            logistics=DicePool([DiceType.D6]),
            security=DicePool([DiceType.D6]),
            intelligence=DicePool([DiceType.D6]),
        )
        state.subordinates = [agent]
        state.tasks = []
        state.completed_tasks = []
        state.events_log = []
        return state, agent

    def test_duration_task_completes_on_fifth_tick_and_releases_agent(self):
        state, agent = self.make_state_with_one_agent()
        state.add_task(
            "Five Tick Test",
            GovernanceArea.INTELLIGENCE,
            duration_ticks=5,
        )
        self.assertTrue(
            state.assign_subordinate_to_task(agent.name, "Five Tick Test")
        )

        # Random events and resource amounts are irrelevant to this test.
        with patch.object(state, "_generate_random_event"):
            with patch("gdsa.simulation.random.random", return_value=1.0):
                for expected_progress in range(1, 5):
                    state.advance_tick()
                    self.assertEqual(state.completed_tasks, [])
                    self.assertEqual(len(state.tasks), 1)
                    self.assertEqual(state.tasks[0].progress, expected_progress)
                    self.assertEqual(agent.current_task, "Five Tick Test")

                state.advance_tick()

        self.assertEqual(len(state.completed_tasks), 1)
        self.assertEqual(state.completed_tasks[0].name, "Five Tick Test")
        self.assertEqual(state.tasks, [])
        self.assertIsNone(agent.current_task)
        self.assertIsNone(state.completed_tasks[0].assigned_subordinate)
        self.assertTrue(any("completed!" in event for event in state.events_log))

    def test_busy_agent_cannot_be_assigned_to_second_task(self):
        state, agent = self.make_state_with_one_agent()
        state.add_task("First", GovernanceArea.LOGISTICS, required_progress=100)
        state.add_task("Second", GovernanceArea.SECURITY, required_progress=100)

        self.assertTrue(state.assign_subordinate_to_task(agent.name, "First"))
        self.assertFalse(state.assign_subordinate_to_task(agent.name, "Second"))
        self.assertEqual(agent.current_task, "First")

    def test_task_cannot_be_assigned_to_two_agents(self):
        state, agent = self.make_state_with_one_agent()
        second = Subordinate(
            name="Second Administrator",
            logistics=DicePool([DiceType.D3]),
            security=DicePool([DiceType.D3]),
            intelligence=DicePool([DiceType.D3]),
        )
        state.subordinates.append(second)
        state.add_task("Exclusive Task", GovernanceArea.LOGISTICS, required_progress=100)

        self.assertTrue(state.assign_subordinate_to_task(agent.name, "Exclusive Task"))
        self.assertFalse(
            state.assign_subordinate_to_task(second.name, "Exclusive Task")
        )
        self.assertIsNone(second.current_task)

    def test_skill_task_uses_agent_domain_roll(self):
        state, agent = self.make_state_with_one_agent()
        state.add_task("Skill Task", GovernanceArea.LOGISTICS, required_progress=100)
        self.assertTrue(state.assign_subordinate_to_task(agent.name, "Skill Task"))

        with patch.object(agent, "roll_for_area", return_value=4):
            with patch("gdsa.simulation.random.random", return_value=1.0):
                state.advance_tick()

        self.assertEqual(state.tasks[0].progress, 4)

    def test_missing_agent_pauses_task_without_crashing(self):
        state, _agent = self.make_state_with_one_agent()
        state.add_task("Orphaned Task", GovernanceArea.LOGISTICS, required_progress=100)
        state.tasks[0].assigned_subordinate = "Missing Agent"

        with patch("gdsa.simulation.random.random", return_value=1.0):
            state.advance_tick()

        self.assertIsNone(state.tasks[0].assigned_subordinate)
        self.assertTrue(
            any("paused because its assigned subordinate is missing" in event
                for event in state.events_log)
        )


if __name__ == "__main__":
    unittest.main()
