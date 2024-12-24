import os
import random
import string
import asyncio
import discord
from discord.ext import commands, tasks

# Install discord.py-self if not already installed
os.system('pip install discord.py-self && pip install --upgrade pip')

# Create a bot instance with sharding (manual control)
bot = commands.Bot(command_prefix="!", help_command=None, self_bot=True)
bot.channel = None

from dotenv import load_dotenv
 

# Load environment variables (still necessary for other environment-related settings)
load_dotenv()

token = os.getenv("TOKEN")



# Maximum messages before hard stop
MAX_MESSAGES = 100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

# Delay settings
initial_delay = 0.001  # Start with 1 ms delay for push mode
max_delay = 1.0  # Maximum delay of 1 second
min_delay = 0.2  # Minimum delay of 0.7 seconds

# Task to spam messages with random intervals and incremental delay
@tasks.loop(seconds=2)
async def spam():
    if bot.channel is None:
        bot.channel = bot.get_channel(1278580578593148978)  # Your channel ID here

    if bot.channel is not None:
        try:
            # Generate random text
            text = ''.join(random.sample(string.ascii_letters + string.digits, 40))

            # Send the message
            await bot.channel.send(text)
            print(f"Sent message: {text}")

            # Random cooldown to simulate tug-of-war or varying delay to avoid rate limits
            cooldown = random.uniform(1, 3)  # Cooldown between 1 and 5 seconds
            await asyncio.sleep(cooldown)

        except discord.HTTPException as e:
            print(f"Failed to send message due to rate limit or server error: {e}")

@spam.before_loop
async def before_spam():
    await bot.wait_until_ready()

# Task for self-pinging to keep the bot alive
@tasks.loop(seconds=60)  # Ping every 60 seconds
async def self_pinger():
    try:
        if bot.channel is not None:
            await bot.channel.send("Pong!")
    except discord.HTTPException as e:
        print(f"Error during self-ping: {e}")

@self_pinger.before_loop
async def before_self_pinger():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    spam.start()  # Start the spam task when the bot is ready
    self_pinger.start()  # Start the self-pinger to keep the bot alive

bot.run(TOKEN)
