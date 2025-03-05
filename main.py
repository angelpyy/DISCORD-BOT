import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.data_manager import initialize_data_files

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Bot initialization
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Bot startup events
@bot.event
async def setup_hook():
    # Initialize data files
    initialize_data_files()
    
    # Load all cogs
    await bot.load_extension("cogs.stats_commands")
    await bot.load_extension("cogs.competition_commands")
    
    # Sync commands
    await bot.tree.sync()
    print("Synced commands")
    
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)