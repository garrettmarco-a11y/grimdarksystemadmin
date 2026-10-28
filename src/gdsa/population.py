"""Population groups and food-linked contentedness. Must not depend on Tkinter.

Group state is hidden from the player; only the derived public-order status is shown
in the normal interface. Values are prototype parameters (see docs/GAME_DESIGN.md).
"""

from dataclasses import dataclass
from typing import List

CONTENTEDNESS_MIN = 0
CONTENTEDNESS_MAX = 100
WEEKLY_RECOVERY = 2  # Per fully fed upkeep, up to the group's baseline

# (minimum weighted contentedness, public-order status), highest first
PUBLIC_ORDER_THRESHOLDS = [
    (50, "Stable"),
    (35, "Strained"),
    (20, "Discontented"),
    (CONTENTEDNESS_MIN, "Unrest"),
]

@dataclass
class PopulationGroup:
    """A fixed population group with hidden contentedness"""
    name: str
    population: int  # Thousands; fixed for now
    food_demand: int  # Biologics per weekly upkeep
    baseline: int  # Starting contentedness and recovery ceiling
    max_shortage_penalty: int  # Contentedness lost when the group gets no food at all
    contentedness: int = 0

@dataclass
class GroupChange:
    """What one weekly upkeep did to one group"""
    name: str
    demand: int
    fed: int
    before: int
    after: int

    @property
    def delta(self) -> int:
        return self.after - self.before

def starting_groups() -> List[PopulationGroup]:
    """The starting groups, in feeding-priority order (fed first to last)"""
    groups = [
        PopulationGroup("Nobles", 20, 1, 70, 8),
        PopulationGroup("Free Traders", 80, 2, 60, 12),
        PopulationGroup("Proles", 900, 7, 55, 20),
    ]
    for group in groups:
        group.contentedness = group.baseline
    return groups

def feed_groups(groups: List[PopulationGroup], food_available: int) -> List[GroupChange]:
    """Feed groups in priority order from the food available and update contentedness.

    A fully fed group recovers WEEKLY_RECOVERY up to its baseline. A group short of its
    demand loses its maximum penalty scaled by the unmet fraction, rounded up.
    """
    food = max(food_available, 0)
    changes = []
    for group in groups:
        fed = min(group.food_demand, food)
        food -= fed
        unmet = group.food_demand - fed
        before = group.contentedness
        if unmet:
            penalty = -(-unmet * group.max_shortage_penalty // group.food_demand)
            group.contentedness = max(CONTENTEDNESS_MIN, before - penalty)
        elif before < group.baseline:
            group.contentedness = min(group.baseline, before + WEEKLY_RECOVERY)
        changes.append(GroupChange(group.name, group.food_demand, fed, before, group.contentedness))
    return changes

def weighted_contentedness(groups: List[PopulationGroup]) -> int:
    """Population-weighted average contentedness, rounded down"""
    total = sum(group.population for group in groups)
    return sum(group.population * group.contentedness for group in groups) // total

def public_order_status(contentedness: int) -> str:
    """Broad public-order status for a weighted contentedness value"""
    for minimum, status in PUBLIC_ORDER_THRESHOLDS:
        if contentedness >= minimum:
            return status
    return PUBLIC_ORDER_THRESHOLDS[-1][1]
