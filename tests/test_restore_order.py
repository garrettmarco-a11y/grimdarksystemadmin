import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.models import GovernanceArea, ResourceType  # noqa: E402
from gdsa.simulation import FOOD_RIOTS_EVENT, GameState, add_starting_tasks  # noqa: E402

RESTORE_ORDER = "Restore Order in the Lower Hab-Blocks"
OTHER_EVENTS = (
    "Asteroid mining yields extra minerals!",
    "Equipment malfunction - materials needed for repairs.",
    "Merchant convoy arrives with trade opportunities.",
    "Heretic cell discovered in the manufacturing district.",
)


def quiet_tick(state):
    """Advance one tick with no random event and no resource generation."""
    with patch("gdsa.simulation.random.random", return_value=1.0):
        with patch("gdsa.simulation.random.randint", return_value=0):
            state.advance_tick()


def event_tick(state, event_text, amount=7):
    """Advance one tick in which the given random event is selected; generation adds nothing."""
    def randint(a, b):
        return amount if (a, b) in ((5, 10), (3, 7), (3, 8)) else 0

    with patch("gdsa.simulation.random.random", return_value=0.0):
        with patch("gdsa.simulation.random.choice", return_value=event_text):
            with patch("gdsa.simulation.random.randint", side_effect=randint):
                state.advance_tick()


def stock(state):
    r = state.resources
    return (r.materials, r.biologics, r.minerals)


class RestoreOrderTaskTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        add_starting_tasks(self.state)
        self.state.imperial_tribute_due = 1000  # Keep tribute out of these resource checks
        self.agent = self.state.subordinates[0]

    def task(self):
        return next(t for t in self.state.tasks if t.name == RESTORE_ORDER)

    def assign(self):
        return self.state.assign_subordinate_to_task(self.agent.name, RESTORE_ORDER)

    def complete(self):
        self.assertTrue(self.assign())
        for _ in range(5):
            quiet_tick(self.state)

    # 1. Availability

    def test_available_at_start_with_correct_definition(self):
        task = self.task()
        self.assertEqual(task.area, GovernanceArea.SECURITY)
        self.assertEqual((task.duration_ticks, task.required_progress, task.progress), (5, 5, 0))
        self.assertEqual(task.cost, {ResourceType.MATERIALS: 5})
        self.assertEqual(task.rewards, {})
        self.assertTrue(task.prevents_next_food_riot)
        self.assertIsNone(task.assigned_subordinate)
        for phrase in ("5 Materials", "5 days", "food riot", "No resource reward"):
            self.assertIn(phrase, task.description)

    def test_existing_starting_tasks_remain(self):
        names = [t.name for t in self.state.tasks]
        for name in ("Requisition Food Stores", "Commission Emergency Food Convoy",
                     "Test Action: Administrative Audit"):
            self.assertIn(name, names)

    def test_other_starting_tasks_do_not_grant_protection(self):
        self.assertEqual(
            [t.name for t in self.state.tasks if t.prevents_next_food_riot], [RESTORE_ORDER]
        )

    # 2-3. Cost

    def test_assignment_deducts_exactly_five_materials(self):
        self.assertTrue(self.assign())
        self.assertEqual(stock(self.state), (45, 30, 20))
        self.assertEqual(self.agent.current_task, RESTORE_ORDER)
        self.assertIn(
            f"Day 1: {self.agent.name} assigned to {RESTORE_ORDER}; 5 Materials spent.",
            self.state.events_log,
        )

    def test_insufficient_materials_rejected_without_state_change(self):
        self.state.resources.materials = 4
        self.assertEqual(
            self.state.assignment_error(self.agent.name, RESTORE_ORDER),
            f"Not enough Materials: {RESTORE_ORDER} costs 5 Materials, but only 4 are available.",
        )
        self.assertFalse(self.assign())
        self.assertEqual(stock(self.state), (4, 30, 20))
        self.assertIsNone(self.agent.current_task)
        self.assertIsNone(self.task().assigned_subordinate)
        self.assertFalse(self.state.food_riot_protection)
        self.assertEqual(self.state.events_log, [])

    def test_exactly_five_materials_is_enough(self):
        self.state.resources.materials = 5
        self.assertTrue(self.assign())
        self.assertEqual(self.state.resources.materials, 0)

    # 4-6. Activation

    def test_protection_inactive_at_start_and_before_completion(self):
        self.assertFalse(self.state.food_riot_protection)
        self.assertTrue(self.assign())
        for expected in range(1, 5):
            quiet_tick(self.state)
            self.assertEqual(self.task().progress, expected)
            self.assertFalse(self.state.food_riot_protection)

    def test_food_riot_before_completion_is_not_prevented(self):
        self.assertTrue(self.assign())
        quiet_tick(self.state)
        event_tick(self.state, FOOD_RIOTS_EVENT, amount=7)
        self.assertEqual(self.state.resources.biologics, 23)
        self.assertIn(f"Day 3: {FOOD_RIOTS_EVENT}", self.state.events_log)

    def test_completion_activates_protection_logs_and_releases(self):
        self.complete()
        self.assertTrue(self.state.food_riot_protection)
        self.assertEqual([t.name for t in self.state.completed_tasks], [RESTORE_ORDER])
        self.assertNotIn(RESTORE_ORDER, [t.name for t in self.state.tasks])
        self.assertIsNone(self.agent.current_task)
        self.assertIn(f"Day 6: Task '{RESTORE_ORDER}' completed!", self.state.events_log)
        self.assertIn(
            "Day 6: Order holds in the lower hab-blocks. The next food riot will be suppressed.",
            self.state.events_log,
        )
        self.assertEqual(sum("will be suppressed" in e for e in self.state.events_log), 1)

    def test_completion_grants_no_resource_reward(self):
        self.complete()
        self.assertEqual(stock(self.state), (45, 30, 20))
        self.assertFalse(any("delivers" in e for e in self.state.events_log))

    def test_completed_task_cannot_be_reassigned(self):
        self.complete()
        self.assertFalse(self.assign())
        self.assertEqual(self.state.resources.materials, 45)

    # 7-8. Prevention

    def test_food_riot_prevented_and_protection_consumed(self):
        self.complete()
        event_tick(self.state, FOOD_RIOTS_EVENT, amount=7)
        self.assertEqual(self.state.resources.biologics, 30)
        self.assertFalse(self.state.food_riot_protection)
        self.assertNotIn(f"Day 7: {FOOD_RIOTS_EVENT}", self.state.events_log)
        self.assertIn(
            "Day 7: Food riots threatened the lower sectors, but Security forces suppressed them. "
            "No biologics lost; the protection is spent.",
            self.state.events_log,
        )

    def test_second_food_riot_is_not_prevented(self):
        self.complete()
        event_tick(self.state, FOOD_RIOTS_EVENT, amount=7)
        event_tick(self.state, FOOD_RIOTS_EVENT, amount=6)
        self.assertEqual(self.state.resources.biologics, 24)
        self.assertIn(f"Day 8: {FOOD_RIOTS_EVENT}", self.state.events_log)
        self.assertEqual(sum("suppressed them" in e for e in self.state.events_log), 1)
        self.assertFalse(self.state.food_riot_protection)

    # 9. Other events unaffected

    def test_other_events_unaffected_and_do_not_consume_protection(self):
        expected = {
            OTHER_EVENTS[0]: (45, 30, 27),  # +7 Minerals
            OTHER_EVENTS[1]: (38, 30, 20),  # -7 Materials
            OTHER_EVENTS[2]: (45, 30, 20),
            OTHER_EVENTS[3]: (45, 30, 20),
        }
        for text, resources in expected.items():
            with self.subTest(event=text):
                self.setUp()
                self.complete()
                event_tick(self.state, text, amount=7)
                self.assertEqual(stock(self.state), resources)
                self.assertIn(f"Day 7: {text}", self.state.events_log)
                self.assertTrue(self.state.food_riot_protection)

    def test_unprotected_other_events_match_protected_outcome(self):
        protected = self.state
        self.complete()
        for text in OTHER_EVENTS:
            with self.subTest(event=text):
                plain = GameState()
                plain.resources.materials = 45
                plain.day = protected.day
                before = stock(protected)
                with patch("gdsa.simulation.random.choice", return_value=text):
                    with patch("gdsa.simulation.random.randint", return_value=4):
                        protected._generate_random_event()
                        plain._generate_random_event()
                delta_protected = tuple(a - b for a, b in zip(stock(protected), before))
                delta_plain = tuple(a - b for a, b in zip(stock(plain), (45, 30, 20)))
                self.assertEqual(delta_protected, delta_plain)
                self.assertEqual(protected.events_log[-1], plain.events_log[-1])
                self.assertTrue(protected.food_riot_protection)

    # 10. Persistence

    def test_protection_persists_across_ticks_without_riots(self):
        self.complete()
        for _ in range(30):
            quiet_tick(self.state)
            self.assertTrue(self.state.food_riot_protection)
        event_tick(self.state, OTHER_EVENTS[2])
        self.assertTrue(self.state.food_riot_protection)
        event_tick(self.state, FOOD_RIOTS_EVENT)
        self.assertFalse(self.state.food_riot_protection)

    # 11. Event selection and probability unchanged

    def test_event_selection_list_and_order_unchanged(self):
        with patch("gdsa.simulation.random.choice", side_effect=lambda seq: seq[0]) as choice:
            self.state._generate_random_event()
        self.assertEqual(
            choice.call_args[0][0],
            [OTHER_EVENTS[0], FOOD_RIOTS_EVENT, OTHER_EVENTS[1], OTHER_EVENTS[2], OTHER_EVENTS[3]],
        )

    def test_event_chance_unchanged_with_protection_active(self):
        self.state.food_riot_protection = True
        with patch.object(self.state, "_generate_random_event") as event:
            for roll in (0.0999, 0.1, 0.5):
                with patch("gdsa.simulation.random.random", return_value=roll):
                    self.state.advance_tick()
        self.assertEqual(event.call_count, 1)

    def test_food_riot_without_protection_unchanged(self):
        event_tick(self.state, FOOD_RIOTS_EVENT, amount=8)
        self.assertEqual(self.state.resources.biologics, 22)
        self.assertEqual(self.state.events_log, [f"Day 2: {FOOD_RIOTS_EVENT}"])


if __name__ == "__main__":
    unittest.main()
