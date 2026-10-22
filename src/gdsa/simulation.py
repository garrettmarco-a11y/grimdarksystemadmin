"""Game state and simulation rules. Must not depend on Tkinter."""

import random
from typing import List, Optional

from .models import (
    DicePool,
    DiceType,
    GovernanceArea,
    ResourceType,
    Resources,
    Subordinate,
    Task,
)

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
    ):
        """Add a task. Duration-based tasks advance once per tick; skill-based tasks roll for progress."""
        task = Task(
            name,
            area,
            required_progress=duration_ticks if duration_ticks is not None else required_progress,
            description=description,
            duration_ticks=duration_ticks,
        )
        self.tasks.append(task)
    
    def assign_subordinate_to_task(self, subordinate_name: str, task_name: str) -> bool:
        """Assign an available subordinate to an unassigned task."""
        subordinate = next((s for s in self.subordinates if s.name == subordinate_name), None)
        task = next((t for t in self.tasks if t.name == task_name and not t.is_complete), None)
        if subordinate is None or task is None:
            return False
        if subordinate.current_task and subordinate.current_task != task_name:
            return False
        if task.assigned_subordinate and task.assigned_subordinate != subordinate_name:
            return False
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
            "Food riots in the lower sectors - biologics consumed.",
            "Equipment malfunction - materials needed for repairs.",
            "Merchant convoy arrives with trade opportunities.",
            "Heretic cell discovered in the manufacturing district."
        ]
        
        event = random.choice(events)
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
