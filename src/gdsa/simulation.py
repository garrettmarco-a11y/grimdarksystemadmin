"""Game state and simulation rules. Must not depend on Tkinter."""

import random
from typing import Dict, List, Optional

from .models import (
    DicePool,
    DiceType,
    GovernanceArea,
    ResourceType,
    Resources,
    Subordinate,
    Task,
)

# Text of the Food Riots random event; also identifies it for riot protection.
FOOD_RIOTS_EVENT = "Food riots in the lower sectors - biologics consumed."

class GameState:
    """Main game state manager"""
    
    def __init__(self):
        self.day = 1
        self.resources = Resources()
        self.subordinates = self._generate_starting_subordinates()
        self.tasks = []
        self.completed_tasks = []
        self.events_log = []
        self.imperial_tribute_due = 7  # Days until tribute is due
        self.imperial_tribute_amount = 30  # Materials needed
        self.tribute_outcome: Optional[str] = None  # "paid" or "failed" on the tick tribute fell due
        self.food_riot_protection = False  # Suppresses the next Food Riots event, then lapses
        
    def _generate_starting_subordinates(self) -> List[Subordinate]:
        """Generate starting subordinates with random stats"""
        names = [
            "Administrator Vex", "Strategos Korrath", "Courtier Illyana",
            "Overseer Grimm", "Captain Nerys"
        ]
        
        subordinates = []
        for name in names[:3]:  # Start with 3 subordinates
            # Generate random dice pools
            logistics = DicePool([random.choice(list(DiceType))])
            security = DicePool([random.choice(list(DiceType))])
            intelligence = DicePool([random.choice(list(DiceType))])
            
            # Sometimes add a second die
            if random.random() < 0.3:
                logistics.dice.append(random.choice(list(DiceType)))
            if random.random() < 0.3:
                security.dice.append(random.choice(list(DiceType)))
            if random.random() < 0.3:
                intelligence.dice.append(random.choice(list(DiceType)))
            
            # Random need
            needs = [
                "Luxurious quarters", "Rare spices", "Combat stimulants",
                "Information network access", "Personal guard detail", None
            ]
            need = random.choice(needs)
            
            subordinates.append(Subordinate(name, logistics, security, intelligence, need))
        
        return subordinates
    
    def add_task(
        self,
        name: str,
        area: GovernanceArea,
        required_progress: int = 10,
        description: str = "",
        duration_ticks: Optional[int] = None,
        rewards: Optional[Dict[ResourceType, int]] = None,
        cost: Optional[Dict[ResourceType, int]] = None,
        prevents_next_food_riot: bool = False,
    ):
        """Add a task. Duration-based tasks advance once per tick; skill-based tasks roll for progress.
        Cost is paid once, when a subordinate is successfully assigned; rewards are granted once,
        when the task completes."""
        task = Task(
            name,
            area,
            required_progress=duration_ticks if duration_ticks is not None else required_progress,
            description=description,
            duration_ticks=duration_ticks,
            rewards=dict(rewards or {}),
            cost=dict(cost or {}),
            prevents_next_food_riot=prevents_next_food_riot,
        )
        self.tasks.append(task)
    
    def assignment_error(self, subordinate_name: str, task_name: str) -> Optional[str]:
        """Explain why an assignment would be rejected, or return None if it is allowed."""
        subordinate = next((s for s in self.subordinates if s.name == subordinate_name), None)
        task = next((t for t in self.tasks if t.name == task_name and not t.is_complete), None)
        if subordinate is None:
            return f"No subordinate named '{subordinate_name}'."
        if task is None:
            return f"No available task named '{task_name}'."
        if subordinate.current_task and subordinate.current_task != task_name:
            return f"{subordinate_name} is already working on {subordinate.current_task}."
        if task.assigned_subordinate and task.assigned_subordinate != subordinate_name:
            return f"{task_name} is already assigned to {task.assigned_subordinate}."
        if task.assigned_subordinate == subordinate_name:
            return None  # Already assigned; nothing further to pay
        for resource_type, amount in task.cost.items():
            available = self.resources.get(resource_type)
            if available < amount:
                return (
                    f"Not enough {resource_type.value}: {task_name} costs {amount} "
                    f"{resource_type.value}, but only {available} are available."
                )
        return None

    def assign_subordinate_to_task(self, subordinate_name: str, task_name: str) -> bool:
        """Assign an available subordinate to an unassigned task, paying its cost."""
        if self.assignment_error(subordinate_name, task_name) is not None:
            return False
        subordinate = next(s for s in self.subordinates if s.name == subordinate_name)
        task = next(t for t in self.tasks if t.name == task_name and not t.is_complete)
        if task.assigned_subordinate == subordinate_name:
            return True
        for resource_type, amount in task.cost.items():
            self.resources.subtract(resource_type, amount)
        if task.cost:
            spent = ", ".join(f"{amount} {resource_type.value}" for resource_type, amount in task.cost.items())
            self.events_log.append(
                f"Day {self.day}: {subordinate_name} assigned to {task_name}; {spent} spent."
            )
        subordinate.current_task = task_name
        task.assigned_subordinate = subordinate_name
        return True

    def advance_tick(self):
        """Advance the game by one day"""
        self.day += 1
        self.imperial_tribute_due -= 1
        self.tribute_outcome = None
        
        # Process tasks
        for task in self.tasks:
            if task.assigned_subordinate and not task.is_complete:
                subordinate = next(
                    (s for s in self.subordinates if s.name == task.assigned_subordinate),
                    None,
                )
                if subordinate is None:
                    task.assigned_subordinate = None
                    self.events_log.append(
                        f"Day {self.day}: Task '{task.name}' paused because its assigned subordinate is missing."
                    )
                    continue

                progress = 1 if task.duration_ticks is not None else subordinate.roll_for_area(task.area)
                task.progress = min(task.required_progress, task.progress + progress)
                self.events_log.append(
                    f"Day {self.day}: {subordinate.name} made {progress} progress on {task.name}"
                )

                if task.is_complete:
                    self.completed_tasks.append(task)
                    subordinate.current_task = None
                    task.assigned_subordinate = None
                    self.events_log.append(f"Day {self.day}: Task '{task.name}' completed!")
                    for resource_type, amount in task.rewards.items():
                        self.resources.add(resource_type, amount)
                        self.events_log.append(
                            f"Day {self.day}: {task.name} delivers {amount} {resource_type.value} to the hive's stores."
                        )
                    if task.prevents_next_food_riot:
                        self.food_riot_protection = True
                        self.events_log.append(
                            f"Day {self.day}: Order holds in the lower hab-blocks. The next food riot will be suppressed."
                        )

        # Remove completed tasks
        self.tasks = [t for t in self.tasks if not t.is_complete]
        
        # Resource generation (basic)
        self.resources.add(ResourceType.MATERIALS, random.randint(1, 3))
        self.resources.add(ResourceType.BIOLOGICS, random.randint(1, 2))
        self.resources.add(ResourceType.MINERALS, random.randint(0, 2))
        
        # Check imperial tribute
        if self.imperial_tribute_due <= 0:
            self._handle_imperial_tribute()
        
        # Random events (placeholder)
        if random.random() < 0.1:
            self._generate_random_event()
    
    def _handle_imperial_tribute(self):
        """Handle imperial tribute payment"""
        if self.resources.materials >= self.imperial_tribute_amount:
            self.resources.subtract(ResourceType.MATERIALS, self.imperial_tribute_amount)
            self.events_log.append(f"Day {self.day}: Imperial tribute of {self.imperial_tribute_amount} Materials paid.")
            self.imperial_tribute_due = 30  # Next tribute in 30 days
            self.tribute_outcome = "paid"
        else:
            self.events_log.append(f"Day {self.day}: WARNING: Failed to pay Imperial tribute! Consequences incoming...")
            self.imperial_tribute_due = 7  # Grace period
            self.tribute_outcome = "failed"
    
    def _generate_random_event(self):
        """Generate a random event"""
        events = [
            "Asteroid mining yields extra minerals!",
            FOOD_RIOTS_EVENT,
            "Equipment malfunction - materials needed for repairs.",
            "Merchant convoy arrives with trade opportunities.",
            "Heretic cell discovered in the manufacturing district."
        ]
        
        event = random.choice(events)
        if event == FOOD_RIOTS_EVENT and self.food_riot_protection:
            self.food_riot_protection = False
            self.events_log.append(
                f"Day {self.day}: Food riots threatened the lower sectors, but Security forces "
                "suppressed them. No biologics lost; the protection is spent."
            )
            return
        self.events_log.append(f"Day {self.day}: {event}")
        
        # Apply event effects (simplified); losses may push stock into deficit
        if "minerals" in event:
            self.resources.add(ResourceType.MINERALS, random.randint(3, 8))
        elif "biologics consumed" in event:
            self.resources.deduct(ResourceType.BIOLOGICS, random.randint(5, 10))
        elif "materials needed" in event:
            self.resources.deduct(ResourceType.MATERIALS, random.randint(3, 7))


def add_starting_tasks(state: GameState):
    """Add the tasks available at the start of a new game."""
    state.add_task("Improve Mining Operations", GovernanceArea.LOGISTICS, 15,
                   "Increase mineral extraction efficiency")
    state.add_task("Security Patrol Schedule", GovernanceArea.SECURITY, 12,
                   "Organize patrols to maintain order")
    state.add_task("Noble Relations", GovernanceArea.INTELLIGENCE, 20,
                   "Gather intelligence on local noble houses")
    state.add_task(
        "Test Action: Administrative Audit",
        GovernanceArea.INTELLIGENCE,
        duration_ticks=5,
        description="Development test: completes after exactly five simulation ticks.",
    )
    state.add_task(
        "Requisition Food Stores",
        GovernanceArea.LOGISTICS,
        duration_ticks=5,
        description="Commandeer nutrient-paste stocks from the agri-levels. "
                    "After 5 days, adds 10 Biologics to the hive's food supply.",
        rewards={ResourceType.BIOLOGICS: 10},
    )
    state.add_task(
        "Commission Emergency Food Convoy",
        GovernanceArea.LOGISTICS,
        duration_ticks=5,
        description="Pay off-world factors to run a guarded grain convoy. "
                    "Costs 10 Materials when assigned; after 5 days, adds 20 Biologics to the hive's food supply.",
        rewards={ResourceType.BIOLOGICS: 20},
        cost={ResourceType.MATERIALS: 10},
    )
    state.add_task(
        "Restore Order in the Lower Hab-Blocks",
        GovernanceArea.SECURITY,
        duration_ticks=5,
        description="Send enforcers to crush unrest in the lower hab-blocks. "
                    "Costs 5 Materials when assigned; after 5 days, prevents the next food riot. "
                    "No resource reward.",
        cost={ResourceType.MATERIALS: 5},
        prevents_next_food_riot=True,
    )
