import discord
from discord import app_commands
from discord.ext import commands
import datetime
from typing import Optional, Dict, List
import io
import numpy as np

from utils.data_manager import (
    load_health_data, save_health_data, 
    load_competitions, save_competitions,
    get_competition_choices
)
from utils.visualization import create_competition_graph
import config

class CompetitionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="startcomp", description="Start a new fitness competition")
    @app_commands.describe(
        name="Competition name",
        end_date="End date (YYYY-MM-DD)",
        weight="Your starting weight",
        body_fat="Your starting body fat percentage",
        muscle_mass="Your starting muscle mass",
        bmr="Your starting BMR"
    )
    async def startcomp(self, interaction: discord.Interaction, name: str, end_date: str,
                        weight: float, body_fat: float, muscle_mass: float, bmr: float):
        # Check to make sure the comp ends in the future & date format is good
        try:
            end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            if end_datetime < datetime.datetime.now():
                await interaction.response.send_message("End date must be in the future!")
                return
        except ValueError:
            await interaction.response.send_message("Invalid date format. Use YYYY-MM-DD")
            return
        
        comps = load_competitions()
        if name in comps:
            await interaction.response.send_message(f"Competition '{name}' already exists!")
            return
        
        user_id = str(interaction.user.id)
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
        await interaction.response.send_message(
            f"Competition '{name}' created! Others can join using /joincomp {name}"
        )

    @app_commands.command(name="joincomp", description="Join an existing fitness competition")
    @app_commands.describe(
        name="Name of competition to join",
        weight="Your starting weight",
        body_fat="Your starting body fat percentage",
        muscle_mass="Your starting muscle mass",
        bmr="Your starting BMR"
    )
    async def joincomp(self, interaction: discord.Interaction, name: str,
                        weight: float, body_fat: float, muscle_mass: float, bmr: float):
        user_id = str(interaction.user.id)
        
        # Load competitions data
        competitions = load_competitions()
        
        # Check if competition exists
        if name not in competitions:
            await interaction.response.send_message(f"Competition '{name}' doesn't exist!")
            return
        
        # Check if user is already in competition
        if user_id in competitions[name]['participants']:
            await interaction.response.send_message("You're already in this competition!")
            return
        
        # Check if competition end date has passed
        end_date = datetime.datetime.strptime(competitions[name]['end_date'], '%Y-%m-%d')
        if end_date < datetime.datetime.now():
            await interaction.response.send_message("This competition has already ended!")
            return
            
        # Add user to competition with their stats
        competitions[name]['participants'][user_id] = {
            'weight': weight,
            'body_fat': body_fat,
            'muscle_mass': muscle_mass,
            'bmr': bmr
        }
        save_competitions(competitions)
        
        await interaction.response.send_message(f"You've successfully joined '{name}'!")

    @app_commands.command(name="listcomps", description="List all active competitions")
    async def listcomps(self, interaction: discord.Interaction):
        competitions = load_competitions()
        if not competitions:
            await interaction.response.send_message("No active competitions found!")
            return
        
        now = datetime.datetime.now()
        active_comps = []
        past_comps = []
        
        for name, data in competitions.items():
            end_date = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d')
            participants = len(data['participants'])
            
            comp_info = f"**{name}**: {participants} participants, ends {data['end_date']}"
            
            if end_date > now:
                active_comps.append(comp_info)
            else:
                past_comps.append(comp_info)
        
        message = "**Active Competitions:**\n"
        if active_comps:
            message += "\n".join(active_comps)
        else:
            message += "None\n"
        
        message += "\n**Past Competitions:**\n"
        if past_comps:
            message += "\n".join(past_comps)
        else:
            message += "None"
        
        await interaction.response.send_message(message)

    # The autocomplete function for competition names
    async def comp_name_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        competitions = get_competition_choices()
        return [
            app_commands.Choice(name=comp, value=comp)
            for comp in competitions if current.lower() in comp.lower()
        ][:25]  # Discord limits to 25 choices
            
    @app_commands.command(name="compstatus", description="Show competition progress")
    @app_commands.describe(name="Name of the competition")
    @app_commands.autocomplete(name=comp_name_autocomplete)
    async def compstatus(self, interaction: discord.Interaction, name: str):
        # Load competitions and health data
        competitions = load_competitions()
        health_data = load_health_data()
        
        # Check if competition exists
        if name not in competitions:
            await interaction.response.send_message(f"Competition '{name}' doesn't exist!")
            return
            
        competition = competitions[name]
        start_date = datetime.datetime.strptime(competition['start_date'], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(competition['end_date'], '%Y-%m-%d')
        current_date = datetime.datetime.now()
        
        if current_date < start_date:
            await interaction.response.send_message("Competition hasn't started yet!")
            return
        
        # Initialize data structure for tracking progress
        progress_data = {}
        user_names = {}
        
        # For each participant
        for user_id, initial_stats in competition['participants'].items():
            progress_data[user_id] = {
                'dates': [],
                'points': [],
                'body_fat_points': [],
                'muscle_mass_points': [],
                'bmr_points': []
            }
            
            # Try to get user's name
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_names[user_id] = user.name
            except:
                user_names[user_id] = f"User_{user_id[-4:]}"
            
            # Get relevant health data if available
            if user_id in health_data:
                # Process each date with health data from start_date until now or end_date
                for date_str, daily_stats in sorted(health_data[user_id].items()):
                    # Skip dates before start or after end
                    date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    if date < start_date or date > min(end_date, current_date):
                        continue
                        
                    # Calculate relative changes and points
                    bf_change = (initial_stats['body_fat'] - daily_stats['body_fat']) / initial_stats['body_fat'] * 100
                    bf_points = bf_change * config.BF_POINTS_MULTIPLIER
                    
                    mm_change = (daily_stats['muscle_mass'] / initial_stats['muscle_mass'] * 100) - 100
                    mm_points = mm_change * config.MM_POINTS_MULTIPLIER
                    
                    bmr_change = (daily_stats['bmr'] / initial_stats['bmr'] * 100) - 100
                    bmr_points = bmr_change * config.BMR_POINTS_MULTIPLIER
                    
                    total_points = bf_points + mm_points + bmr_points
                    
                    # Store progress
                    progress_data[user_id]['dates'].append(date_str)
                    progress_data[user_id]['points'].append(total_points)
                    progress_data[user_id]['body_fat_points'].append(bf_points)
                    progress_data[user_id]['muscle_mass_points'].append(mm_points)
                    progress_data[user_id]['bmr_points'].append(bmr_points)
        
        # If no progress data, provide message
        if all(len(data['dates']) == 0 for data in progress_data.values()):
            await interaction.response.send_message(
                f"No progress data found for competition '{name}'. Participants need to log their stats using /logstats.")
            return
        
        # Create visualization
        buf = create_competition_graph(name, progress_data, user_names)
        
        # Prepare status message
        status_msg = f"**Competition Status for '{name}'**\n"
        status_msg += f"Start Date: {competition['start_date']}\n"
        status_msg += f"End Date: {competition['end_date']}\n\n"
        
        # Add detailed statistics for each participant
        status_msg += "**Detailed Statistics:**\n"
        for user_id in progress_data:
            if not progress_data[user_id]['dates']:  # Skip if no data
                continue
                
            initial_stats = competition['participants'][user_id]
            current_date = progress_data[user_id]['dates'][-1]
            current_stats = health_data[user_id][current_date]
            
            # Calculate relative changes
            bf_change = ((initial_stats['body_fat'] - current_stats['body_fat']) / initial_stats['body_fat']) * 100
            mm_change = ((current_stats['muscle_mass'] / initial_stats['muscle_mass']) * 100) - 100
            bmr_change = ((current_stats['bmr'] / initial_stats['bmr']) * 100) - 100
            
            # Calculate points
            bf_points = bf_change * config.BF_POINTS_MULTIPLIER
            mm_points = mm_change * config.MM_POINTS_MULTIPLIER
            bmr_points = bmr_change * config.BMR_POINTS_MULTIPLIER
            total_points = bf_points + mm_points + bmr_points
            
            status_msg += f"\n__**{user_names[user_id]}**__\n"
            status_msg += f"Body Fat: {initial_stats['body_fat']}% → {current_stats['body_fat']}% (Change: {bf_change:.2f}%, Points: {bf_points:.2f})\n"
            status_msg += f"Muscle Mass: {initial_stats['muscle_mass']}lbs → {current_stats['muscle_mass']}lbs (Change: {mm_change:.2f}%, Points: {mm_points:.2f})\n"
            status_msg += f"BMR: {initial_stats['bmr']} → {current_stats['bmr']} (Change: {bmr_change:.2f}%, Points: {bmr_points:.2f})\n"
            status_msg += f"Total Points: {total_points:.2f}\n"
        
        status_msg += "\n**Current Standings:**\n"
        final_points = {}
        for user_id in progress_data:
            if progress_data[user_id]['points']:
                final_points[user_names[user_id]] = progress_data[user_id]['points'][-1]
        
        # Sort by points
        sorted_standings = dict(sorted(final_points.items(), key=lambda x: x[1], reverse=True))
        for i, (user_name, points) in enumerate(sorted_standings.items(), 1):
            status_msg += f"{i}. {user_name}: {points:.2f} points\n"
        
        # Send message and plot
        await interaction.response.send_message(
            content=status_msg,
            file=discord.File(buf, filename='competition_progress.png')
        )

async def setup(bot):
    await bot.add_cog(CompetitionCommands(bot))