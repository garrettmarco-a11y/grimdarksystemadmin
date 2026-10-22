"""Core data types: enums, dice pools, subordinates, tasks, and resources."""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

# Skill-based tasks: the assigned subordinate rolls once per this many ticks (days) of work.
SKILL_ROLL_INTERVAL_TICKS = 7

class DiceType(Enum):
    D3 = 3
    D6 = 6
    D10 = 10

class ResourceType(Enum):
    MATERIALS = "Materials"
    BIOLOGICS = "Biologics"
    MINERALS = "Minerals"

class GovernanceArea(Enum):
    LOGISTICS = "Logistics"
    SECURITY = "Security"
    INTELLIGENCE = "Intelligence"

@dataclass
class DicePool:
    """Represents a dice pool like 2D6 or D3+D10"""
    dice: List[DiceType]
    
    def roll(self) -> int:
        """Roll all dice in the pool and return the sum"""
        return sum(random.randint(1, die.value) for die in self.dice)
    
    def __str__(self) -> str:
        if not self.dice:
            return "0"
        
        # Count occurrences of each die type
        counts = {}
        for die in self.dice:
            counts[die] = counts.get(die, 0) + 1
        
        # Format as "2D6+D10" etc.
        parts = []
        for die_type, count in sorted(counts.items(), key=lambda x: x[0].value):
            if count == 1:
                parts.append(f"D{die_type.value}")
            else:
                parts.append(f"{count}D{die_type.value}")
        
        return "+".join(parts)

@dataclass
class Subordinate:
    """Represents a subordinate with their skills and needs"""
    name: str
    logistics: DicePool
    security: DicePool
    intelligence: DicePool
    need: Optional[str] = None
    need_fulfilled: bool = False
    current_task: Optional[str] = None
    
    def get_stat(self, area: GovernanceArea) -> DicePool:
        """Get the dice pool for a specific governance area"""
        if area == GovernanceArea.LOGISTICS:
            return self.logistics
        elif area == GovernanceArea.SECURITY:
            return self.security
        else:
            return self.intelligence
    
    def roll_for_area(self, area: GovernanceArea) -> int:
        """Roll dice for a specific governance area"""
        base_roll = self.get_stat(area).roll()
        bonus = 2 if self.need_fulfilled else 0
        return base_roll + bonus

@dataclass
class Task:
    """Represents a task that can be assigned to subordinates"""
    name: str
    area: GovernanceArea
    progress: int = 0
    required_progress: int = 10
    assigned_subordinate: Optional[str] = None
    description: str = ""
    duration_ticks: Optional[int] = None
    rewards: Dict["ResourceType", int] = field(default_factory=dict)  # Granted on completion
    repeatable: bool = False  # A fresh copy is offered again after completion
    days_worked: int = 0  # Ticks of work by an assigned subordinate
    
    @property
    def is_skill_based(self) -> bool:
        return self.duration_ticks is None
    
    @property
    def days_until_roll(self) -> int:
        """Ticks of work remaining before the next skill roll"""
        return SKILL_ROLL_INTERVAL_TICKS - self.days_worked % SKILL_ROLL_INTERVAL_TICKS
    
    @property
    def is_complete(self) -> bool:
        return self.progress >= self.required_progress
    
    @property
    def completion_percentage(self) -> float:
        return min(100.0, (self.progress / self.required_progress) * 100)

@dataclass
class Resources:
    """Tracks the three main resource types"""
    materials: int = 50
    biologics: int = 30
    minerals: int = 20
    
    def add(self, resource_type: ResourceType, amount: int):
        """Add resources of a specific type"""
        if resource_type == ResourceType.MATERIALS:
            self.materials += amount
        elif resource_type == ResourceType.BIOLOGICS:
            self.biologics += amount
        elif resource_type == ResourceType.MINERALS:
            self.minerals += amount
    
    def subtract(self, resource_type: ResourceType, amount: int) -> bool:
        """Subtract resources if available, return True if successful"""
        if resource_type == ResourceType.MATERIALS:
            if self.materials >= amount:
                self.materials -= amount
                return True
        elif resource_type == ResourceType.BIOLOGICS:
            if self.biologics >= amount:
                self.biologics -= amount
                return True
        elif resource_type == ResourceType.MINERALS:
            if self.minerals >= amount:
                self.minerals -= amount
                return True
        return False

    def deduct(self, resource_type: ResourceType, amount: int):
        """Remove resources unconditionally; stock may fall below zero into deficit."""
        self.add(resource_type, -amount)
