import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.models import GovernanceArea, ResourceType  # noqa: E402
from gdsa.population import feed_groups, starting_groups  # noqa: E402
from gdsa.simulation import (  # noqa: E402
    FOOD_RIOTS_EVENT,
    SECURITY_PRESENCE_PENALTY_PERCENT,
    SECURITY_PRESENCE_UPKEEPS,
    GameState,
    add_starting_tasks,
)

PRESENCE = "Maintain District Security Presence"
RESTORE_ORDER = "Restore Order in the Lower Hab-Blocks"


def quiet_tick(state):
    """Advance one tick with no random event and no resource generation."""
    with patch("gdsa.simulation.random.random", return_value=1.0):
        with patch("gdsa.simulation.random.randint", return_value=0):
            state.advance_tick()


def deltas(changes):
    return tuple(change.delta for change in changes)


class DampenedPenaltyTests(unittest.TestCase):
    # Change from baseline for (Nobles, Free Traders, Proles) by Biologics in store,
    # at 100% (existing rule) and at 90% (security presence). 90% applies to the exact
    # loss before the existing round-up, so small losses can round to the same value.
    EXPECTED = {
        -5: ((-8, -12, -20), (-8, -11, -18)),
        0: ((-8, -12, -20), (-8, -11, -18)),
        1: ((0, -12, -20), (0, -11, -18)),
        2: ((0, -6, -20), (0, -6, -18)),
        3: ((0, 0, -20), (0, 0, -18)),
        4: ((0, 0, -18), (0, 0, -16)),
        5: ((0, 0, -15), (0, 0, -13)),
        6: ((0, 0, -12), (0, 0, -11)),
        7: ((0, 0, -9), (0, 0, -8)),
        8: ((0, 0, -6), (0, 0, -6)),
        9: ((0, 0, -3), (0, 0, -3)),
        10: ((0, 0, 0), (0, 0, 0)),
    }

    def test_percent_constant(self):
        self.assertEqual(SECURITY_PRESENCE_PENALTY_PERCENT, 90)
        self.assertEqual(SECURITY_PRESENCE_UPKEEPS, 4)

    def test_full_and_dampened_outcome_table(self):
        for available, (full, dampened) in self.EXPECTED.items():
            with self.subTest(available=available):
                self.assertEqual(deltas(feed_groups(starting_groups(), available)), full)
                self.assertEqual(deltas(feed_groups(starting_groups(), available, 100)), full)
                self.assertEqual(deltas(feed_groups(starting_groups(), available, 90)), dampened)

    def test_dampening_never_increases_or_erases_a_loss(self):
        for available in range(-2, 11):
            full = deltas(feed_groups(starting_groups(), available))
            damp = deltas(feed_groups(starting_groups(), available, 90))
            for f, d in zip(full, damp):
                self.assertGreaterEqual(d, f)  # Loss is no larger
                if f < 0:
                    self.assertLess(d, 0)  # Loss is never erased

    def test_dampened_loss_is_ceiling_of_ninety_percent_of_exact_loss(self):
        groups = starting_groups()
        changes = feed_groups(groups, 4, 90)  # Proles fed 1 of 7: exact loss 120/7 = 17.14
        self.assertEqual(changes[2].delta, -16)  # ceil(17.14 * 0.9 = 15.43)

    def test_recovery_unchanged_when_dampened(self):
        for percent in (100, 90):
            groups = starting_groups()
            groups[2].contentedness = 40
            feed_groups(groups, 10, percent)
            self.assertEqual(groups[2].contentedness, 42)

    def test_feeding_priority_unchanged_when_dampened(self):
        changes = feed_groups(starting_groups(), 4, 90)
        self.assertEqual([(c.name, c.fed) for c in changes], [("Nobles", 1), ("Free Traders", 2), ("Proles", 1)])


class SecurityPresenceTaskTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        add_starting_tasks(self.state)
        self.state.imperial_tribute_due = 10000
        self.state.resources.materials = 1000
        self.agent = self.state.subordinates[0]

    def task(self):
        return next(t for t in self.state.tasks if t.name == PRESENCE)

    def assign(self):
        self.assertTrue(self.state.assign_subordinate_to_task(self.agent.name, PRESENCE))

    def tick_to(self, day, biologics=None):
        """Quiet ticks up to `day`; optionally fix Biologics before each upkeep."""
        while self.state.day < day:
            if biologics is not None and (self.state.day + 1) % 7 == 0:
                self.state.resources.biologics = biologics
            quiet_tick(self.state)

    def proles(self):
        return self.state.population[2].contentedness

    def test_available_with_correct_definition(self):
        task = self.task()
        self.assertEqual(task.area, GovernanceArea.SECURITY)
        self.assertEqual((task.duration_ticks, task.required_progress, task.progress), (5, 5, 0))
        self.assertEqual(task.cost, {ResourceType.MATERIALS: 5})
        self.assertEqual(task.rewards, {})
        self.assertTrue(task.establishes_security_presence)
        self.assertTrue(task.repeatable)
        self.assertFalse(task.prevents_next_food_riot)
        for phrase in ("5 Materials", "5 days", "food-shortage discontent", "four weekly food upkeeps", "Repeatable"):
            self.assertIn(phrase, task.description)

    def test_assignment_charges_five_materials(self):
        self.assign()
        self.assertEqual(self.state.resources.materials, 995)

    def test_inactive_before_completion_and_upkeep_during_task_is_full_penalty(self):
        self.tick_to(3)
        self.assign()  # Completes on day 8
        self.tick_to(7, biologics=5)
        self.assertEqual(self.state.security_presence_upkeeps, 0)
        self.assertFalse(self.state.last_upkeep_dampened)
        self.assertEqual(self.proles(), 40)  # Full 15-point loss

    def test_completion_activates_without_granting_contentedness(self):
        self.assign()
        before = [g.contentedness for g in self.state.population]
        materials, biologics = self.state.resources.materials, self.state.resources.biologics
        self.tick_to(6)
        self.assertEqual(self.state.security_presence_upkeeps, SECURITY_PRESENCE_UPKEEPS)
        self.assertEqual([g.contentedness for g in self.state.population], before)
        self.assertEqual((self.state.resources.materials, self.state.resources.biologics), (materials, biologics))
        self.assertIn(f"Day 6: Task '{PRESENCE}' completed!", self.state.events_log)
        self.assertIn("Day 6: Enforcer patrols take up posts across the hab-districts.", self.state.events_log)
        self.assertIsNone(self.agent.current_task)

    def test_next_four_upkeeps_dampened_then_expires(self):
        self.assign()  # Completes day 6
        losses, flags, remaining = [], [], []
        for upkeep_day in (7, 14, 21, 28, 35):
            self.state.population[2].contentedness = 55
            self.tick_to(upkeep_day, biologics=5)
            losses.append(55 - self.proles())
            flags.append(self.state.last_upkeep_dampened)
            remaining.append(self.state.security_presence_upkeeps)
        self.assertEqual(losses, [13, 13, 13, 13, 15])
        self.assertEqual(flags, [True, True, True, True, False])
        self.assertEqual(remaining, [3, 2, 1, 0, 0])

    def test_adequately_fed_upkeeps_still_count_toward_expiry(self):
        self.assign()
        self.tick_to(28, biologics=100)
        self.assertEqual(self.state.security_presence_upkeeps, 0)
        self.tick_to(35, biologics=5)
        self.assertFalse(self.state.last_upkeep_dampened)

    def test_completion_on_upkeep_day_dampens_that_upkeep(self):
        self.tick_to(2)
        self.assign()  # Completes day 7, before that tick's upkeep
        self.tick_to(7, biologics=5)
        self.assertTrue(self.state.last_upkeep_dampened)
        self.assertEqual(self.proles(), 42)  # 13-point loss
        self.assertEqual(self.state.security_presence_upkeeps, SECURITY_PRESENCE_UPKEEPS - 1)

    def test_repeatable_copy_offered_and_recharged(self):
        self.assign()
        self.tick_to(6)
        copy = self.task()
        self.assertEqual((copy.progress, copy.assigned_subordinate), (0, None))
        self.assertEqual(copy.cost, {ResourceType.MATERIALS: 5})
        self.assertEqual([t.name for t in self.state.completed_tasks], [PRESENCE])
        self.assign()
        self.assertEqual(self.state.resources.materials, 990)

    def test_completing_again_while_active_refreshes_without_stacking(self):
        self.assign()
        self.tick_to(14)  # Upkeeps on 7 and 14 consume two: 2 remaining
        self.assertEqual(self.state.security_presence_upkeeps, 2)
        self.assign()  # Repeat completes on day 19
        self.tick_to(19)
        self.assertEqual(self.state.security_presence_upkeeps, SECURITY_PRESENCE_UPKEEPS)
        for upkeep_day in (21, 28, 35, 42):
            self.tick_to(upkeep_day)
            self.assertTrue(self.state.last_upkeep_dampened)
        self.tick_to(49)
        self.assertFalse(self.state.last_upkeep_dampened)

    def test_direct_refresh_sets_rather_than_adds(self):
        self.state.security_presence_upkeeps = 3
        self.assign()
        self.tick_to(6)
        self.assertEqual(self.state.security_presence_upkeeps, SECURITY_PRESENCE_UPKEEPS)

    def test_independent_of_restore_order(self):
        self.assign()
        self.tick_to(6)
        self.assertFalse(self.state.food_riot_protection)
        # Presence does not prevent riots
        with patch("gdsa.simulation.random.choice", return_value=FOOD_RIOTS_EVENT), \
                patch("gdsa.simulation.random.randint", return_value=7):
            biologics = self.state.resources.biologics
            self.state._generate_random_event()
        self.assertEqual(self.state.resources.biologics, biologics - 7)

    def test_restore_order_does_not_grant_presence(self):
        self.assertTrue(self.state.assign_subordinate_to_task(self.agent.name, RESTORE_ORDER))
        self.tick_to(6)
        self.assertTrue(self.state.food_riot_protection)
        self.assertEqual(self.state.security_presence_upkeeps, 0)
        self.assertNotIn(RESTORE_ORDER, [t.name for t in self.state.tasks])  # Still one-time

    def test_debug_report_shows_modifier_and_remaining(self):
        self.assertIn("Security presence: inactive", self.state.population_debug_report())
        self.assign()
        self.tick_to(7, biologics=5)
        report = self.state.population_debug_report()
        self.assertIn("Security presence: active, next 3 upkeep(s) apply shortage losses at 90%", report)
        self.assertIn("Last upkeep: Day 7, 5 Biologics in store, shortage losses at 90% (security presence)", report)

    def test_routine_log_does_not_expose_modifier(self):
        for seed in range(20):
            random.seed(seed)
            state = GameState()
            add_starting_tasks(state)
            state.assign_subordinate_to_task(state.subordinates[0].name, PRESENCE)
            for _ in range(120):
                state.advance_tick()
            log = "\n".join(state.events_log)
            for word in ("90%", "Security presence", "dampen", "Proles", "contentedness"):
                self.assertNotIn(word, log)


if __name__ == "__main__":
    unittest.main()
