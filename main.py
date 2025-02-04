import discord
from discord import app_commands
from discord.ext import commands
import json
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import io
import numpy as np
from typing import List, Optional
from dotenv import load_dotenv
import os

### Bot init ###
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

### Bot command sync ###
@bot.event
async def setup_hook():
    initialize_data_file()
    await bot.tree.sync()
    print("Synced commands")
    
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discrodosdsdsdm!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


### Data Management ###
# Create json files if they done exist; add empty json
def initialize_data_file():
    if not Path('health_data.json').exists():
        with open('health_data.json', 'w') as f:
            json.dump({}, f)
    if not Path('competitions.json').exists():
        with open('competitions.json', 'w') as f:
            json.dump({}, f)

# Load the data from the health stat json
def load_health_data():
    with open('health_data.json', 'r') as f:
        return json.load(f)

# Save to the health stat json
def save_health_data(data):
    with open('health_data.json', 'w') as f:
        json.dump(data, f)

# Load the data from the competition json
def load_competitions():
    with open('competitions.json', 'r') as f:
        return json.load(f)

# Save to the competition json
def save_competitions(data):
    with open('competitions.json', 'w') as f:
        json.dump(data, f)

### Define slash commands ###
# log stats
@bot.tree.command(name="logstats", description="record ur shitty scale measurements for today")
@app_commands.describe(
    weight="your weight in lbs", 
    body_fat="your body fat %/%/%/%", 
    muscle_mass="muscle mass in lbs", 
    bmr="how many calories u burn lil bro"
)
async def logstats(interactions: discord.Interaction, weight: float,
                    body_fat: float, muscle_mass: float, bmr: float):
    user_id = str(interactions.user.id)
    
    # grab today in YYYY-MM-DD format
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # import entire health json
    data = load_health_data()
    
    # check if user has ever logged into health before, if not create dict for them
    if user_id not in data:
        data[user_id] = {}

    # check if user has already logged their stats for today :)
    if today in data[user_id]:
        await interactions.response.send_message('You already recorded your metrics today. Use /editweight to modify them.')
        return
    
    # if u made it here, not logged today...
    data[user_id][today] = {
        'weight': weight,
        'body_fat': body_fat,
        'muscle_mass': muscle_mass,
        'bmr': bmr
    }
    
    # hahgagag lets save 
    save_health_data(data)
    
    # response to user
    response = f'Weight recorded: {weight} lbs'
    if body_fat: response += f'\nBody Fat: {body_fat}%'
    if muscle_mass: response += f'\nMuscle Mass: {muscle_mass} lbs'
    if bmr: response += f'\nBMR: {bmr} cal'
    
    # by bye
    await interactions.response.send_message(response)
    
# edit stats in case ur a fuck up
@bot.tree.command(name="editstats", description="edit your recorded stats for today")
@app_commands.describe(
    weight="your weight in lbs", 
    body_fat="your body fat %", 
    muscle_mass="muscle mass in lbs",
    bmr="how many calories u burn"
)
async def editstats(interactions: discord.Interaction, 
                    weight: Optional[float] = None,
                    body_fat: Optional[float] = None, 
                    muscle_mass: Optional[float] = None,
                    bmr: Optional[float] = None):
    user_id = str(interactions.user.id)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Load data
    data = load_health_data()
    
    # Check if user has data
    if user_id not in data:
        await interactions.response.send_message("You haven't logged any stats yet. Use /logstats first.")
        return
        
    # Check if user has logged today
    if today not in data[user_id]:
        await interactions.response.send_message("You haven't logged any stats today. Use /logstats first.")
        return
    
    # Update only provided values
    if weight is not None:
        data[user_id][today]['weight'] = weight
    if body_fat is not None:
        data[user_id][today]['body_fat'] = body_fat
    if muscle_mass is not None:
        data[user_id][today]['muscle_mass'] = muscle_mass
    if bmr is not None:
        data[user_id][today]['bmr'] = bmr
        
    # Save changes
    save_health_data(data)
    
    # Prepare response message
    response = "Updated values:"
    if weight is not None:
        response += f"\nWeight: {weight} lbs"
    if body_fat is not None:
        response += f"\nBody Fat: {body_fat}%"
    if muscle_mass is not None:
        response += f"\nMuscle Mass: {muscle_mass} lbs"
    if bmr is not None:
        response += f"\nBMR: {bmr}"
        
    await interactions.response.send_message(response)

@bot.tree.command(name="startcomp", description="ermmm 1v1")
@app_commands.describe(
    name="comp name",
    end_date="till when sire (YYYY-MM-DD)",
    weight="starting weight",
    body_fat="starting bf%",
    muscle_mass="starting muscle mass",
    bmr="starting bmr"
)
async def startcomp(interactions: discord.Interaction, name: str, end_date: str,
                    weight: float, body_fat: float, muscle_mass: float, bmr: float):
    # check to make sure the comp ends in not today (if made today) & date format is good
    try:
        end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        if end_datetime < datetime.datetime.now():
            await interactions.response.send_message("End date must be in the future!")
            return
    except ValueError:
        await interactions.response.send_message("Invalid date format. Use YYYY-MM-DD")
        return
    
    comps = load_competitions()
    if name in comps:
        await interactions.response.send_message(f"'{name}' already exists pal")
        return
    
    user_id = str(interactions.user.id)
    comps[name] = {
        'start_date': datetime.datetime.now().strftime('%Y-%m-%d'),
        'end_date': end_date,
        'participants': {
            user_id: {
                'weight': weight,
                'body_fat': body_fat,
                'muscle_mass': muscle_mass,
                'bmr': bmr
    }
        },
        'creator': user_id
    }
    
    save_competitions(comps)
    await interactions.response.send_message(
        f"Competition '{name}' created! Others can join using /joincomp {name}"
    )

@bot.tree.command(name="joincomp", description="join some comp")
@app_commands.describe(
    name="name of competition to join",
    weight="starting weight",
    body_fat="starting bf%",
    muscle_mass="starting muscle mass",
    bmr="starting bmr"
)
async def joincomp(interactions: discord.Interaction, name: str,
                    weight: float, body_fat: float, muscle_mass: float, bmr: float):
    user_id = str(interactions.user.id)
    
    # Load competitions data
    competitions = load_competitions()
    
    # Check if competition exists
    if name not in competitions:
        await interactions.response.send_message(f"Competition '{name}' doesn't exist!")
        return
    
    # Check if user is already in competition
    if user_id in competitions[name]['participants']:
        await interactions.response.send_message("You're already in this competition!")
        return
    
    # Check if competition end date has passed
    end_date = datetime.datetime.strptime(competitions[name]['end_date'], '%Y-%m-%d')
    if end_date < datetime.datetime.now():
        await interactions.response.send_message("This competition has already ended!")
        return
        
    # Add user to competition with their stats
    competitions[name]['participants'][user_id] = {
        'weight': weight,
        'body_fat': body_fat,
        'muscle_mass': muscle_mass,
        'bmr': bmr
    }
    save_competitions(competitions)
    
    await interactions.response.send_message(f"You've successfully joined '{name}'!")

@bot.tree.command(name="listcomps", description="List all active competitions")
async def listcomps(interactions: discord.Interaction):
    competitions = load_competitions()
    if not competitions:
        await interactions.response.send_message("No active competitions found!")
        return
    
    message = "Active Competitions:\n"
    for name, data in competitions.items():
        participants = len(data['participants'])
        message += f"- {name}: {participants} participants, ends {data['end_date']}\n"
    
    await interactions.response.send_message(message)

@bot.tree.command(name="progress", description="Display your progress graph")
@app_commands.describe(
    weight="Show weight progress (True/False)",
    body_fat="Show body fat % progress (True/False)", 
    muscle_mass="Show muscle mass progress (True/False)",
    bmr="Show BMR progress (True/False)"
)
async def progress(interactions: discord.Interaction,
                    weight: Optional[bool] = None,
                    body_fat: Optional[bool] = None,
                    muscle_mass: Optional[bool] = None, 
                    bmr: Optional[bool] = None):
    
    user_id = str(interactions.user.id)
    data = load_health_data()

    # Check if user has data
    if user_id not in data:
        await interactions.response.send_message("No data found! Use /logstats first.")
        return

    # If no options selected, default to weight only
    if all(x is None for x in [weight, body_fat, muscle_mass, bmr]):
        weight = True
        body_fat = muscle_mass = bmr = False
    # If any option is True, set others to False if they're None
    elif any(x is True for x in [weight, body_fat, muscle_mass, bmr]):
        weight = weight if weight is not None else False
        body_fat = body_fat if body_fat is not None else False
        muscle_mass = muscle_mass if muscle_mass is not None else False
        bmr = bmr if bmr is not None else False

    # Convert data to pandas DataFrame
    df = pd.DataFrame.from_dict(data[user_id], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Count how many plots we need
    plots_needed = sum([weight, body_fat, muscle_mass, bmr])
    if plots_needed == 0:
        await interactions.response.send_message("Please select at least one metric to display.")
        return
    # Create subplot grid
    plt.style.use('dark_background')
    fig, axs = plt.subplots(plots_needed, 1, figsize=(10, 6*plots_needed))
    
    # If only one plot, axs needs to be in a list
    if plots_needed == 1:
        axs = [axs]

    current_plot = 0

    # Create individual plots
    if weight:
        axs[current_plot].plot(df.index, df['weight'], 'g-', label='Weight (lbs)')
        axs[current_plot].set_title('Weight Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()
        current_plot += 1

    if body_fat:
        axs[current_plot].plot(df.index, df['body_fat'], 'r-', label='Body Fat %')
        axs[current_plot].set_title('Body Fat Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()
        current_plot += 1

    if muscle_mass:
        axs[current_plot].plot(df.index, df['muscle_mass'], 'b-', label='Muscle Mass (lbs)')
        axs[current_plot].set_title('Muscle Mass Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()
        current_plot += 1

    if bmr:
        axs[current_plot].plot(df.index, df['bmr'], 'y-', label='BMR (cal)')
        axs[current_plot].set_title('BMR Progress')
        axs[current_plot].grid(True, alpha=0.3)
        axs[current_plot].legend()

    fig.suptitle(f'Health Progress for {interactions.user.name}', fontsize=16)
    plt.tight_layout()
    # Save plot to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Clean up matplotlib
    plt.close()

    # Send plot as Discord attachment
    await interactions.response.send_message(
        file=discord.File(buf, filename='progress.png')
    )

@bot.tree.command(name="compstatus", description="Show competition progress")
@app_commands.describe(
    name="name of the competition"
)
async def compstatus(interactions: discord.Interaction, name: str):
    # Load competitions and health data
    competitions = load_competitions()
    health_data = load_health_data()
    
    # Check if competition exists
    if name not in competitions:
        await interactions.response.send_message(f"Competition '{name}' doesn't exist!")
        return
        
    competition = competitions[name]
    start_date = datetime.datetime.strptime(competition['start_date'], '%Y-%m-%d')
    end_date = datetime.datetime.strptime(competition['end_date'], '%Y-%m-%d')
    current_date = datetime.datetime.now()
    
    if current_date < start_date:
        await interactions.response.send_message("Competition hasn't started yet!")
        return
    
    # Initialize data structure for tracking progress
    progress_data = {}
    
    # For each participant
    for user_id, initial_stats in competition['participants'].items():
        progress_data[user_id] = {
            'dates': [],
            'points': [],
            'body_fat_points': [],
            'muscle_mass_points': [],
            'bmr_points': []
        }
        
        # Get all dates from start to current/end date
        current_date = min(datetime.datetime.now(), end_date)
        date_range = [start_date + datetime.timedelta(days=x) for x in range((current_date - start_date).days + 1)]
        
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            
            # Skip if no health data for this date
            if user_id not in health_data or date_str not in health_data[user_id]:
                continue
                
            daily_stats = health_data[user_id][date_str]
            
            # Calculate relative changes and points
            bf_change = (initial_stats['body_fat'] - daily_stats['body_fat']) / initial_stats['body_fat'] * 100
            bf_points = bf_change * 2  # 1 point per 0.5% reduction
            
            mm_change = (daily_stats['muscle_mass'] / initial_stats['muscle_mass'] * 100) - 100
            mm_points = mm_change  # 1 point per 1% increase
            
            bmr_change = (daily_stats['bmr'] / initial_stats['bmr'] * 100) - 100
            bmr_points = bmr_change  # 1 point per 1% increase
            
            total_points = bf_points + mm_points + bmr_points
            
            # Store progress
            progress_data[user_id]['dates'].append(date_str)
            progress_data[user_id]['points'].append(total_points)
            progress_data[user_id]['body_fat_points'].append(bf_points)
            progress_data[user_id]['muscle_mass_points'].append(mm_points)
            progress_data[user_id]['bmr_points'].append(bmr_points)
    
    # Create visualization
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16))
    
    # Plot total points progression
    for user_id in progress_data:
        user = await bot.fetch_user(int(user_id))
        ax1.plot(progress_data[user_id]['dates'], 
                progress_data[user_id]['points'], 
                marker='o', 
                label=user.name)
    
    ax1.set_title('Total Points Progress')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Total Points')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Plot points breakdown
    bottom = np.zeros(len(next(iter(progress_data.values()))['dates']))
    
    for user_id in progress_data:
        user = await bot.fetch_user(int(user_id))
        dates = progress_data[user_id]['dates']
        
        # Stacked bar for the last date
        idx = -1  # Last date
        ax2.bar(user.name, 
                progress_data[user_id]['body_fat_points'][idx],
                label='Body Fat Points', 
                color='red')
        ax2.bar(user.name, 
                progress_data[user_id]['muscle_mass_points'][idx],
                bottom=progress_data[user_id]['body_fat_points'][idx],
                label='Muscle Mass Points', 
                color='blue')
        ax2.bar(user.name, 
                progress_data[user_id]['bmr_points'][idx],
                bottom=progress_data[user_id]['body_fat_points'][idx] + progress_data[user_id]['muscle_mass_points'][idx],
                label='BMR Points', 
                color='green')
    
    ax2.set_title('Current Points Breakdown')
    ax2.set_ylabel('Points')
    ax2.grid(True, alpha=0.3)
    handles, labels = ax2.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax2.legend(by_label.values(), by_label.keys())
    
    plt.tight_layout()
    
    # Save plot to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Prepare status message
    status_msg = f"**Competition Status for {name}**\n"
    status_msg += f"Start Date: {competition['start_date']}\n"
    status_msg += f"End Date: {competition['end_date']}\n\n"
    
    # Add detailed statistics for each participant
    status_msg += "**Detailed Statistics:**\n"
    for user_id in progress_data:
        if not progress_data[user_id]['dates']:  # Skip if no data
            continue
            
        user = await bot.fetch_user(int(user_id))
        initial_stats = competition['participants'][user_id]
        current_date = progress_data[user_id]['dates'][-1]
        current_stats = health_data[user_id][current_date]
        
        # Calculate relative changes
        bf_change = ((initial_stats['body_fat'] - current_stats['body_fat']) / initial_stats['body_fat']) * 100
        mm_change = ((current_stats['muscle_mass'] / initial_stats['muscle_mass']) * 100) - 100
        bmr_change = ((current_stats['bmr'] / initial_stats['bmr']) * 100) - 100
        
        # Calculate points
        bf_points = bf_change * 2  # 1 point per 0.5% reduction
        mm_points = mm_change     # 1 point per 1% increase
        bmr_points = bmr_change   # 1 point per 1% increase
        total_points = bf_points + mm_points + bmr_points
        
        status_msg += f"\n__**{user.name}**__\n"
        status_msg += f"Body Fat: {initial_stats['body_fat']}% → {current_stats['body_fat']}% (Change: {bf_change:.2f}%, Points: {bf_points:.2f})\n"
        status_msg += f"Muscle Mass: {initial_stats['muscle_mass']}lbs → {current_stats['muscle_mass']}lbs (Change: {mm_change:.2f}%, Points: {mm_points:.2f})\n"
        status_msg += f"BMR: {initial_stats['bmr']} → {current_stats['bmr']} (Change: {bmr_change:.2f}%, Points: {bmr_points:.2f})\n"
        status_msg += f"Total Points: {total_points:.2f}\n"
    
    status_msg += "\n**Current Standings:**\n"
    final_points = {}
    for user_id in progress_data:
        if progress_data[user_id]['points']:
            user = await bot.fetch_user(int(user_id))
            final_points[user.name] = progress_data[user_id]['points'][-1]
    
    # Sort by points
    sorted_standings = dict(sorted(final_points.items(), key=lambda x: x[1], reverse=True))
    for i, (user_name, points) in enumerate(sorted_standings.items(), 1):
        status_msg += f"{i}. {user_name}: {points:.2f} points\n"
    
    # Send message and plot
    await interactions.response.send_message(
        content=status_msg,
        file=discord.File(buf, filename='competition_progress.png')
    )


load_dotenv()
# Add your bot token here
TOKEN = os.getenv('TOKEN')

# Run the bot
bot.run(TOKEN)
