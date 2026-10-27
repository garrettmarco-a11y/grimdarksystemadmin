import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.models import GovernanceArea, ResourceType  # noqa: E402
from gdsa.simulation import (  # noqa: E402
    FOOD_RIOTS_EVENT,
    FOOD_UPKEEP_AMOUNT,
    FOOD_UPKEEP_INTERVAL_DAYS,
    GameState,
)


def quiet_tick(state):
    """Advance one tick with no random event and no resource generation."""
    with patch("gdsa.simulation.random.random", return_value=1.0):
        with patch("gdsa.simulation.random.randint", return_value=0):
            state.advance_tick()


def ticks_to_day(state, day):
    while state.day < day:
        quiet_tick(state)


def upkeep_lines(state):
    return [e for e in state.events_log if "Food upkeep" in e or "FOOD SHORTAGE" in e]


class FoodUpkeepScheduleTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.state.imperial_tribute_due = 1000  # Keep tribute out of these checks

    def test_values(self):
        self.assertEqual((FOOD_UPKEEP_INTERVAL_DAYS, FOOD_UPKEEP_AMOUNT), (7, 10))

    def test_no_upkeep_before_day_seven(self):
        ticks_to_day(self.state, 6)
        self.assertEqual(self.state.resources.biologics, 30)
        self.assertEqual(upkeep_lines(self.state), [])

    def test_first_upkeep_on_day_seven(self):
        ticks_to_day(self.state, 7)
        self.assertEqual(self.state.resources.biologics, 20)
        self.assertEqual(upkeep_lines(self.state), ["Day 7: Food upkeep: the hive consumes 10 Biologics."])

    def test_upkeep_every_seven_days_exactly_once_per_upkeep_day(self):
        self.state.resources.biologics = 1000
        charged_days = []
        for _ in range(50):
            before = self.state.resources.biologics
            quiet_tick(self.state)
            spent = before - self.state.resources.biologics
            self.assertIn(spent, (0, FOOD_UPKEEP_AMOUNT))
            if spent:
                charged_days.append(self.state.day)
        self.assertEqual(charged_days, [7, 14, 21, 28, 35, 42, 49])
        self.assertEqual(len(upkeep_lines(self.state)), 7)

    def test_days_until_next_upkeep(self):
        self.assertEqual(self.state.food_upkeep_due_in, 6)
        expected = {2: 5, 6: 1, 7: 7, 8: 6, 13: 1, 14: 7}
        for day, due_in in expected.items():
            ticks_to_day(self.state, day)
            self.assertEqual(self.state.food_upkeep_due_in, due_in, f"day {day}")


class FoodUpkeepStockTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.state.imperial_tribute_due = 1000
        ticks_to_day(self.state, 6)

    def upkeep_tick(self, biologics):
        self.state.resources.biologics = biologics
        quiet_tick(self.state)
        self.assertEqual(self.state.day, 7)

    def test_sufficient_stock_reduced_by_exactly_ten(self):
        self.upkeep_tick(25)
        self.assertEqual(self.state.resources.biologics, 15)

    def test_exactly_ten_is_sufficient(self):
        self.upkeep_tick(10)
        self.assertEqual(self.state.resources.biologics, 0)
        self.assertEqual(upkeep_lines(self.state), ["Day 7: Food upkeep: the hive consumes 10 Biologics."])

    def test_shortage_consumes_only_what_is_in_store(self):
        self.upkeep_tick(4)
        self.assertEqual(self.state.resources.biologics, 0)
        self.assertEqual(
            upkeep_lines(self.state),
            ["Day 7: FOOD SHORTAGE: upkeep needed 10 Biologics but only 4 were in store. "
             "The hive went 6 short."],
        )

    def test_shortage_from_existing_event_deficit_consumes_nothing(self):
        # Random events may still leave Biologics negative; upkeep never deepens it.
        self.upkeep_tick(-3)
        self.assertEqual(self.state.resources.biologics, -3)
        self.assertIn("only 0 were in store. The hive went 10 short.", upkeep_lines(self.state)[0])

    def test_shortage_is_not_carried_as_debt(self):
        self.upkeep_tick(4)
        self.state.resources.biologics = 12  # Restocked before the next upkeep
        ticks_to_day(self.state, 14)
        self.assertEqual(self.state.resources.biologics, 2)
        self.assertEqual(sum("FOOD SHORTAGE" in e for e in self.state.events_log), 1)
        self.assertIn("Day 14: Food upkeep: the hive consumes 10 Biologics.", self.state.events_log)

    def test_upkeep_affects_only_biologics(self):
        self.upkeep_tick(30)
        r = self.state.resources
        self.assertEqual((r.materials, r.minerals), (50, 20))

    def test_upkeep_uses_no_randomness(self):
        def forbidden(*_args, **_kwargs):
            raise AssertionError("food upkeep must not use randomness")

        with patch("gdsa.simulation.random.random", side_effect=forbidden), \
                patch("gdsa.simulation.random.randint", side_effect=forbidden), \
                patch("gdsa.simulation.random.choice", side_effect=forbidden):
            self.state._handle_food_upkeep()
        self.assertEqual(self.state.resources.biologics, 20)


class FoodUpkeepTickOrderTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.state.imperial_tribute_due = 1000
        ticks_to_day(self.state, 6)

    def test_daily_generation_counts_before_upkeep(self):
        self.state.resources.biologics = 9
        with patch("gdsa.simulation.random.random", return_value=1.0):
            with patch("gdsa.simulation.random.randint", return_value=1):
                self.state.advance_tick()
        self.assertEqual(self.state.resources.biologics, 0)
        self.assertNotIn("FOOD SHORTAGE", " ".join(self.state.events_log))

    def test_task_reward_counts_before_upkeep(self):
        self.state.add_task("Harvest", GovernanceArea.LOGISTICS, duration_ticks=1,
                            rewards={ResourceType.BIOLOGICS: 10})
        self.assertTrue(self.state.assign_subordinate_to_task(self.state.subordinates[0].name, "Harvest"))
        self.state.resources.biologics = 0
        quiet_tick(self.state)
        self.assertEqual(self.state.resources.biologics, 0)
        self.assertNotIn("FOOD SHORTAGE", " ".join(self.state.events_log))

    def test_upkeep_logged_before_tribute_and_events(self):
        self.state.imperial_tribute_due = 1
        with patch("gdsa.simulation.random.random", return_value=0.0):
            with patch("gdsa.simulation.random.choice", return_value=FOOD_RIOTS_EVENT):
                with patch("gdsa.simulation.random.randint", side_effect=lambda a, b: 5 if (a, b) == (5, 10) else 0):
                    self.state.advance_tick()
        day7 = [e for e in self.state.events_log if e.startswith("Day 7:")]
        self.assertEqual(
            day7,
            [
                "Day 7: Food upkeep: the hive consumes 10 Biologics.",
                "Day 7: Imperial tribute of 30 Materials paid.",
                f"Day 7: {FOOD_RIOTS_EVENT}",
            ],
        )
        self.assertEqual(self.state.resources.biologics, 30 - 10 - 5)

    def test_event_roll_happens_once_on_upkeep_and_non_upkeep_days(self):
        for _ in range(2):  # Day 7 (upkeep), then day 8 (none)
            with patch("gdsa.simulation.random.random", return_value=1.0) as roll:
                with patch("gdsa.simulation.random.randint", return_value=0):
                    self.state.advance_tick()
            self.assertEqual(roll.call_count, 1)


if __name__ == "__main__":
    unittest.main()
