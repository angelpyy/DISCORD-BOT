from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
from models.user_stats import UserStats

@dataclass
class CompetitionParticipant:
    """Class for storing competition participant data"""
    user_id: str
    initial_stats: UserStats
    
    @classmethod
    def from_dict(cls, user_id: str, data: Dict[str, Any]) -> 'CompetitionParticipant':
        """Create CompetitionParticipant from dictionary data"""
        return cls(
            user_id=user_id,
            initial_stats=UserStats.from_dict(data)
        )

@dataclass
class Competition:
    """Class for storing competition data"""
    name: str
    start_date: str
    end_date: str
    creator: str
    participants: Dict[str, CompetitionParticipant] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'Competition':
        """Create Competition from dictionary data"""
        participants = {}
        for user_id, participant_data in data.get('participants', {}).items():
            participants[user_id] = CompetitionParticipant.from_dict(user_id, participant_data)
            
        return cls(
            name=name,
            start_date=data.get('start_date', ''),
            end_date=data.get('end_date', ''),
            creator=data.get('creator', ''),
            participants=participants
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Competition to dictionary for storage"""
        participants_dict = {}
        for user_id, participant in self.participants.items():
            participants_dict[user_id] = participant.initial_stats.to_dict()
            
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'creator': self.creator,
            'participants': participants_dict
        }
    
    def is_active(self) -> bool:
        """Check if competition is currently active"""
        now = datetime.now()
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        return start_date <= now <= end_date
    
    def has_ended(self) -> bool:
        """Check if competition has ended"""
        now = datetime.now()
        end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        return now > end_date