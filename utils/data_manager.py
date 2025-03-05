import json
import os
from pathlib import Path
import config

def initialize_data_files():
    """Create JSON files if they don't exist; add empty JSON"""
    # Create data directory if it doesn't exist
    Path("data").mkdir(exist_ok=True)
    
    # Initialize health data file
    if not Path(config.HEALTH_DATA_PATH).exists():
        with open(config.HEALTH_DATA_PATH, 'w') as f:
            json.dump({}, f)
    
    # Initialize competitions file
    if not Path(config.COMPETITIONS_PATH).exists():
        with open(config.COMPETITIONS_PATH, 'w') as f:
            json.dump({}, f)

def load_health_data():
    """Load the data from the health stat json"""
    with open(config.HEALTH_DATA_PATH, 'r') as f:
        return json.load(f)

def save_health_data(data):
    """Save to the health stat json"""
    with open(config.HEALTH_DATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_competitions():
    """Load the data from the competition json"""
    with open(config.COMPETITIONS_PATH, 'r') as f:
        return json.load(f)

def save_competitions(data):
    """Save to the competition json"""
    with open(config.COMPETITIONS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def get_competition_choices():
    """Get a list of competitions for dropdown menus"""
    competitions = load_competitions()
    return [name for name in competitions.keys()]

def get_user_stats(user_id, date=None):
    """Get a user's stats for a specific date or all dates"""
    data = load_health_data()
    if user_id not in data:
        return None
    
    if date:
        return data[user_id].get(date)
    return data[user_id]