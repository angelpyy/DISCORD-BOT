import datetime
import random
import json

# Start date - 3 months ago from 2025-02-03
start_date = datetime.datetime(2024, 11, 3)
end_date = datetime.datetime(2025, 2, 3)

# Initial values
initial_weight = 160
initial_body_fat = 41.2
initial_muscle_mass = 82.6
initial_bmr = 1250.0

# Create data dictionary
data = {"763266960623796235": {}}

# Generate daily entries with a slight downward trend for weight/fat and upward for muscle
current_date = start_date
while current_date <= end_date:
    # Calculate days passed for trending
    days_passed = (current_date - start_date).days
    
    # Calculate trending values with some random variation
    weight = initial_weight - (days_passed * 0.02) + random.uniform(-0.5, 0.5)
    body_fat = initial_body_fat - (days_passed * 0.01) + random.uniform(-0.2, 0.2)
    muscle_mass = initial_muscle_mass + (days_passed * 0.01) + random.uniform(-0.3, 0.3)
    bmr = initial_bmr + (days_passed * 0.07) + random.uniform(-5, 5)
    
    # Format date as string
    date_str = current_date.strftime('%Y-%m-%d')
    
    # Add entry to dictionary
    data["763266960623796235"][date_str] = {
        "weight": round(weight, 1),
        "body_fat": round(body_fat, 1),
        "muscle_mass": round(muscle_mass, 1),
        "bmr": round(bmr, 0)
    }
    
    # Move to next day
    current_date += datetime.timedelta(days=1)

print(json.dumps(data, indent=2))