from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class UserStats:
    """Class for storing user health statistics"""
    weight: float
    body_fat: float
    muscle_mass: float
    bmr: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserStats':
        """Create UserStats instance from dictionary data"""
        return cls(
            weight=data.get('weight', 0.0),
            body_fat=data.get('body_fat', 0.0),
            muscle_mass=data.get('muscle_mass', 0.0),
            bmr=data.get('bmr', 0.0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UserStats to dictionary for storage"""
        return {
            'weight': self.weight,
            'body_fat': self.body_fat,
            'muscle_mass': self.muscle_mass,
            'bmr': self.bmr
        }
    
    def calculate_changes(self, initial_stats: 'UserStats') -> Dict[str, float]:
        """Calculate percentage changes from initial stats"""
        bf_change = ((initial_stats.body_fat - self.body_fat) / initial_stats.body_fat) * 100
        mm_change = ((self.muscle_mass / initial_stats.muscle_mass) * 100) - 100
        bmr_change = ((self.bmr / initial_stats.bmr) * 100) - 100
        
        return {
            'body_fat_change': bf_change,
            'muscle_mass_change': mm_change,
            'bmr_change': bmr_change
        }