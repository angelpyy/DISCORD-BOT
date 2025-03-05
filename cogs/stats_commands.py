import discord
from discord import app_commands
from discord.ext import commands
import datetime
from typing import Optional
import io

from utils.data_manager import load_health_data, save_health_data
from utils.visualization import create_personal_progress_graph

class StatsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="logstats", description="Record your health measurements for today")
    @app_commands.describe(
        weight="Your weight in lbs", 
        body_fat="Your body fat percentage", 
        muscle_mass="Muscle mass in lbs", 
        bmr="How many calories you burn daily"
    )
    async def logstats(self, interaction: discord.Interaction, weight: float,
                        body_fat: float, muscle_mass: float, bmr: float):
        user_id = str(interaction.user.id)
        
        # Grab today in YYYY-MM-DD format
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Import entire health json
        data = load_health_data()
        
        # Check if user has ever logged before, if not create dict for them
        if user_id not in data:
            data[user_id] = {}

        # Check if user has already logged their stats for today
        if today in data[user_id]:
            await interaction.response.send_message('You already recorded your metrics today. Use /editstats to modify them.')
            return
        
        # Not logged today, add the stats
        data[user_id][today] = {
            'weight': weight,
            'body_fat': body_fat,
            'muscle_mass': muscle_mass,
            'bmr': bmr
        }
        
        # Save the updated data
        save_health_data(data)
        
        # Response to user
        response = f'✅ Stats recorded for {today}:\n'
        response += f'• Weight: {weight} lbs\n'
        response += f'• Body Fat: {body_fat}%\n'
        response += f'• Muscle Mass: {muscle_mass} lbs\n'
        response += f'• BMR: {bmr} cal'
        
        await interaction.response.send_message(response)
    
    @app_commands.command(name="editstats", description="Edit your recorded stats for today")
    @app_commands.describe(
        weight="Your weight in lbs", 
        body_fat="Your body fat percentage", 
        muscle_mass="Muscle mass in lbs",
        bmr="How many calories you burn daily"
    )
    async def editstats(self, interaction: discord.Interaction, 
                        weight: Optional[float] = None,
                        body_fat: Optional[float] = None, 
                        muscle_mass: Optional[float] = None,
                        bmr: Optional[float] = None):
        user_id = str(interaction.user.id)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Load data
        data = load_health_data()
        
        # Check if user has data
        if user_id not in data:
            await interaction.response.send_message("You haven't logged any stats yet. Use /logstats first.")
            return
            
        # Check if user has logged today
        if today not in data[user_id]:
            await interaction.response.send_message("You haven't logged any stats today. Use /logstats first.")
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
        response = "✅ Updated values:"
        if weight is not None:
            response += f"\n• Weight: {weight} lbs"
        if body_fat is not None:
            response += f"\n• Body Fat: {body_fat}%"
        if muscle_mass is not None:
            response += f"\n• Muscle Mass: {muscle_mass} lbs"
        if bmr is not None:
            response += f"\n• BMR: {bmr}"
            
        await interaction.response.send_message(response)

    @app_commands.command(name="progress", description="Display your progress graph")
    @app_commands.describe(
        weight="Show weight progress",
        body_fat="Show body fat percentage progress", 
        muscle_mass="Show muscle mass progress",
        bmr="Show BMR progress"
    )
    async def progress(self, interaction: discord.Interaction,
                        weight: Optional[bool] = None,
                        body_fat: Optional[bool] = None,
                        muscle_mass: Optional[bool] = None, 
                        bmr: Optional[bool] = None):
        
        user_id = str(interaction.user.id)
        data = load_health_data()

        # Check if user has data
        if user_id not in data:
            await interaction.response.send_message("No data found! Use /logstats first.")
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

        # Count how many plots we need
        plots_needed = sum([weight, body_fat, muscle_mass, bmr])
        if plots_needed == 0:
            await interaction.response.send_message("Please select at least one metric to display.")
            return
            
        # Generate the graph
        buf = create_personal_progress_graph(
            user_id, 
            interaction.user.name, 
            data,
            show_weight=weight,
            show_body_fat=body_fat,
            show_muscle_mass=muscle_mass,
            show_bmr=bmr
        )

        # Send plot as Discord attachment
        await interaction.response.send_message(
            file=discord.File(buf, filename='progress.png')
        )

async def setup(bot):
    await bot.add_cog(StatsCommands(bot))