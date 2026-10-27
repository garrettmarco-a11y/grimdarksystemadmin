import copy
import json
import random
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gdsa.population import (  # noqa: E402
    PUBLIC_ORDER_THRESHOLDS,
    WEEKLY_RECOVERY,
    feed_groups,
    public_order_status,
    starting_groups,
    weighted_contentedness,
)
from gdsa.simulation import FOOD_UPKEEP_AMOUNT, GameState, add_starting_tasks  # noqa: E402

GROUP_NAMES = ("Nobles", "Free Traders", "Proles")
DEMOGRAPHIC_WORDS = GROUP_NAMES + ("contentedness", "Contentedness")


def quiet_tick(state):
    """Advance one tick with no random event and no resource generation."""
    with patch("gdsa.simulation.random.random", return_value=1.0):
        with patch("gdsa.simulation.random.randint", return_value=0):
            state.advance_tick()


def contentedness(groups):
    return {group.name: group.contentedness for group in groups}


class StartingGroupTests(unittest.TestCase):
    def test_groups_in_feeding_order_with_documented_values(self):
        groups = starting_groups()
        self.assertEqual(
            [(g.name, g.population, g.food_demand, g.baseline, g.max_shortage_penalty, g.contentedness)
             for g in groups],
            [
                ("Nobles", 20, 1, 70, 8, 70),
                ("Free Traders", 80, 2, 60, 12, 60),
                ("Proles", 900, 7, 55, 20, 55),
            ],
        )

    def test_group_demand_matches_existing_upkeep(self):
        self.assertEqual(sum(g.food_demand for g in starting_groups()), FOOD_UPKEEP_AMOUNT)

    def test_new_game_starts_stable(self):
        state = GameState()
        self.assertEqual(weighted_contentedness(state.population), 55)
        self.assertEqual(state.public_order, "Stable")
        self.assertIsNone(state.last_upkeep_day)
        self.assertEqual(state.last_upkeep_changes, [])

    def test_each_game_has_independent_groups(self):
        first, second = GameState(), GameState()
        first.population[2].contentedness = 1
        self.assertEqual(second.population[2].contentedness, 55)


class FeedingRuleTests(unittest.TestCase):
    # Change from baseline for (Nobles, Free Traders, Proles) by Biologics in store.
    EXPECTED_DELTAS = {
        -5: (-8, -12, -20),
        0: (-8, -12, -20),
        1: (0, -12, -20),
        2: (0, -6, -20),
        3: (0, 0, -20),
        4: (0, 0, -18),
        5: (0, 0, -15),
        6: (0, 0, -12),
        7: (0, 0, -9),
        8: (0, 0, -6),
        9: (0, 0, -3),
        10: (0, 0, 0),
    }

    def test_outcome_for_every_amount_in_store(self):
        for available, deltas in self.EXPECTED_DELTAS.items():
            with self.subTest(available=available):
                groups = starting_groups()
                changes = feed_groups(groups, available)
                self.assertEqual(tuple(c.delta for c in changes), deltas)
                self.assertEqual([c.name for c in changes], list(GROUP_NAMES))
                self.assertEqual(sum(c.fed for c in changes), min(max(available, 0), FOOD_UPKEEP_AMOUNT))

    def test_fed_amounts_follow_priority(self):
        changes = feed_groups(starting_groups(), 4)
        self.assertEqual([(c.fed, c.demand) for c in changes], [(1, 1), (2, 2), (1, 7)])

    def test_proles_most_affected_by_any_shortage(self):
        for available in range(-1, FOOD_UPKEEP_AMOUNT):
            changes = feed_groups(starting_groups(), available)
            self.assertEqual(min(changes, key=lambda c: c.delta).name, "Proles")

    def test_surplus_beyond_demand_is_not_used(self):
        self.assertEqual([c.fed for c in feed_groups(starting_groups(), 500)], [1, 2, 7])

    def test_recovery_is_gradual_and_capped_at_baseline(self):
        groups = starting_groups()
        feed_groups(groups, 5)
        self.assertEqual(groups[2].contentedness, 40)
        history = []
        for _ in range(9):
            feed_groups(groups, FOOD_UPKEEP_AMOUNT)
            history.append(groups[2].contentedness)
        self.assertEqual(WEEKLY_RECOVERY, 2)
        self.assertEqual(history, [42, 44, 46, 48, 50, 52, 54, 55, 55])
        self.assertEqual(contentedness(groups)["Nobles"], 70)

    def test_group_above_baseline_is_left_alone_when_fed(self):
        groups = starting_groups()
        groups[0].contentedness = 90
        feed_groups(groups, FOOD_UPKEEP_AMOUNT)
        self.assertEqual(groups[0].contentedness, 90)

    def test_contentedness_floors_at_zero(self):
        groups = starting_groups()
        for _ in range(5):
            feed_groups(groups, 0)
        self.assertEqual(contentedness(groups), {"Nobles": 30, "Free Traders": 0, "Proles": 0})


class PublicOrderThresholdTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(
            PUBLIC_ORDER_THRESHOLDS,
            [(50, "Stable"), (35, "Strained"), (20, "Discontented"), (0, "Unrest")],
        )

    def test_boundaries(self):
        cases = {100: "Stable", 50: "Stable", 49: "Strained", 35: "Strained", 34: "Discontented",
                 20: "Discontented", 19: "Unrest", 0: "Unrest"}
        for value, status in cases.items():
            with self.subTest(value=value):
                self.assertEqual(public_order_status(value), status)

    def test_weighted_average_rounds_down(self):
        groups = starting_groups()
        groups[2].contentedness = 49  # 900*49 + 80*60 + 20*70 = 50300 -> 50.3
        self.assertEqual(weighted_contentedness(groups), 50)
        groups[2].contentedness = 48  # 49400 -> 49.4
        self.assertEqual(weighted_contentedness(groups), 49)
        self.assertEqual(public_order_status(weighted_contentedness(groups)), "Strained")

    def test_examples_from_design(self):
        cases = {5: "Strained", 0: "Strained"}
        for available, status in cases.items():
            groups = starting_groups()
            feed_groups(groups, available)
            self.assertEqual(public_order_status(weighted_contentedness(groups)), status)
        groups = starting_groups()
        for _ in range(3):
            feed_groups(groups, 0)
        self.assertEqual(public_order_status(weighted_contentedness(groups)), "Unrest")


class UpkeepIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.state.imperial_tribute_due = 1000

    def test_contentedness_updates_only_on_upkeep_days(self):
        self.state.resources.biologics = 1000
        self.state.population[2].contentedness = 30
        changed_days = []
        for _ in range(30):
            before = self.state.population[2].contentedness
            quiet_tick(self.state)
            if self.state.population[2].contentedness != before:
                changed_days.append(self.state.day)
                self.assertEqual(self.state.population[2].contentedness - before, WEEKLY_RECOVERY)
        self.assertEqual(changed_days, [7, 14, 21, 28])
        self.assertEqual(self.state.last_upkeep_day, 28)

    def test_shortage_week_through_the_tick(self):
        while self.state.day < 6:
            quiet_tick(self.state)
        self.state.resources.biologics = 5
        quiet_tick(self.state)
        self.assertEqual(self.state.resources.biologics, 0)
        self.assertEqual(contentedness(self.state.population), {"Nobles": 70, "Free Traders": 60, "Proles": 40})
        self.assertEqual(self.state.last_upkeep_available, 5)
        self.assertEqual(self.state.public_order, "Strained")
        self.assertEqual(
            self.state.events_log,
            [
                "Day 7: FOOD SHORTAGE: upkeep needed 10 Biologics but only 5 were in store. The hive went 5 short.",
                "Day 7: Public order in the hive is now Strained.",
            ],
        )

    def test_status_logged_only_when_it_changes_and_on_recovery(self):
        self.state.population[2].contentedness = 45  # Weighted 46 -> Strained
        self.state.resources.biologics = 1000
        for _ in range(13):  # Day 7: Proles 47 (weighted 48, Strained); Day 14: 49 (weighted 50, Stable)
            quiet_tick(self.state)
        status_lines = [e for e in self.state.events_log if "Public order" in e]
        self.assertEqual(status_lines, ["Day 14: Public order in the hive is now Stable."])

    def test_adequate_supply_logs_no_status_when_already_stable(self):
        self.state.resources.biologics = 1000
        for _ in range(14):
            quiet_tick(self.state)
        self.assertFalse(any("Public order" in e for e in self.state.events_log))

    def test_routine_log_never_exposes_demographics(self):
        for seed in range(30):
            random.seed(seed)
            state = GameState()
            add_starting_tasks(state)
            for _ in range(200):
                state.advance_tick()
            log = "\n".join(state.events_log)
            for word in DEMOGRAPHIC_WORDS:
                self.assertNotIn(word, log)


class DebugReportTests(unittest.TestCase):
    def snapshot(self, state):
        return copy.deepcopy((
            state.day, state.population, state.resources, state.events_log, state.tasks,
            state.last_upkeep_day, state.last_upkeep_available, state.last_upkeep_changes,
            state.food_riot_protection, state.imperial_tribute_due,
        ))

    def test_report_exposes_required_details(self):
        state = GameState()
        state.imperial_tribute_due = 1000
        while state.day < 6:
            quiet_tick(state)
        state.resources.biologics = 5
        quiet_tick(state)
        report = state.population_debug_report()
        self.assertTrue(report.startswith("DEBUG"))
        for fragment in (
            "Nobles                 20k       1       70        70            8",
            "Free Traders           80k       2       60        60           12",
            "Proles                900k       7       40        55           20",
            "Weighted contentedness: 42 -> Public order: Strained",
            "Thresholds: Stable >= 50, Strained >= 35, Discontented >= 20, Unrest >= 0",
            "Last upkeep: Day 7, 5 Biologics in store",
            "Proles         fed 2/7  contentedness 55 -> 40 (-15)",
            "Nobles         fed 1/1  contentedness 70 -> 70 (+0)",
        ):
            self.assertIn(fragment, report)

    def test_report_before_any_upkeep(self):
        self.assertIn("Last upkeep: none yet", GameState().population_debug_report())

    def test_report_does_not_mutate_state(self):
        state = GameState()
        add_starting_tasks(state)
        state.resources.biologics = 3
        state._handle_food_upkeep()
        before = self.snapshot(state)
        for _ in range(3):
            state.population_debug_report()
        self.assertEqual(self.snapshot(state), before)


UI_PROBE = r"""
import json, sys
from unittest.mock import MagicMock
for name in ("tkinter", "tkinter.ttk", "tkinter.messagebox", "tkinter.scrolledtext"):
    sys.modules[name] = MagicMock()
sys.path.insert(0, sys.argv[1])
import tkinter
from tkinter import ttk, scrolledtext
import gdsa.ui as ui
gui = ui.GDSAGui(MagicMock(), debug=sys.argv[2] == "debug")
gui.game.resources.biologics = 5
gui.game._handle_food_upkeep()
gui._update_display()
texts = [str(c.kwargs.get("text", "")) for c in ttk.Label.call_args_list]
texts += [str(c.kwargs.get("text", "")) for c in ttk.Label.return_value.config.call_args_list]
tabs = [str(c.kwargs.get("text", "")) for c in ttk.Notebook.return_value.add.call_args_list]
inserted = [str(c.args[1]) for c in scrolledtext.ScrolledText.return_value.insert.call_args_list]
print(json.dumps({"texts": texts, "tabs": tabs, "inserted": inserted,
                  "order_label": gui.public_order_label.config.call_args_list[-1].kwargs["text"]}))
"""


class InterfaceVisibilityTests(unittest.TestCase):
    def probe(self, mode):
        result = subprocess.run(
            [sys.executable, "-c", UI_PROBE, str(ROOT / "src"), mode],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_normal_interface_shows_only_broad_status(self):
        out = self.probe("normal")
        self.assertNotIn("DEBUG: Population", out["tabs"])
        self.assertIn("Public Order: Stable", out["texts"])
        self.assertIn("⚠️ Public Order: Strained", out["texts"])
        visible = "\n".join(out["texts"] + out["tabs"] + out["inserted"])
        for word in DEMOGRAPHIC_WORDS:
            self.assertNotIn(word, visible)

    def test_debug_flag_adds_labelled_read_only_tab(self):
        out = self.probe("debug")
        self.assertIn("DEBUG: Population", out["tabs"])
        self.assertTrue(any(text.startswith("DEBUG - hidden population state") for text in out["inserted"]))
        self.assertTrue(any("Proles" in text for text in out["inserted"]))

    def test_launcher_flag_parsing(self):
        code = (
            "import sys; from unittest.mock import MagicMock\n"
            "for n in ('tkinter','tkinter.ttk','tkinter.messagebox','tkinter.scrolledtext'):\n"
            "    sys.modules[n] = MagicMock()\n"
            f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
            "import gdsa.app as app\n"
            "app.GDSAGui = MagicMock()\n"
            "app.main([]); app.main(['--debug'])\n"
            "print([c.kwargs['debug'] for c in app.GDSAGui.call_args_list])\n"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[False, True]")


if __name__ == "__main__":
    unittest.main()
