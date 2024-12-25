import os
import random
import string
import asyncio
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from aiohttp import web

# Load environment variables
load_dotenv()
token = os.getenv("TOKEN")

# Create a bot instance with sharding (manual control)
bot = commands.Bot(command_prefix="!", help_command=None, self_bot=True)
bot.channel = None

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared state for bot task control
bot_running = {"spam": True}

# Maximum messages before hard stop
MAX_MESSAGES = 1e6  # Adjust as needed

# Delay settings
initial_delay = 0.001  # Start with 1 ms delay for push mode
max_delay = 1.0  # Maximum delay of 1 second
min_delay = 0.2  # Minimum delay of 0.2 seconds

# Task to spam messages
@tasks.loop(seconds=3)
async def spam():
    if bot.channel is None:
        bot.channel = bot.get_channel(1278580578593148978)  # Your channel ID here

    if bot.channel is not None and bot_running["spam"]:
        try:
            text = ''.join(random.sample(string.ascii_letters + string.digits, 40))
            await bot.channel.send(text)
            print(f"Sent message: {text}")
            cooldown = random.uniform(1, 3)  # Cooldown between 1 and 3 seconds
            await asyncio.sleep(cooldown)
        except discord.HTTPException as e:
            logger.error(f"Failed to send message: {e}")

@spam.before_loop
async def before_spam():
    await bot.wait_until_ready()

# Task for self-pinging to keep the bot alive
@tasks.loop(seconds=60)
async def self_pinger():
    if bot.channel is not None and bot_running["spam"]:
        try:
            await bot.channel.send("Pong!")
        except discord.HTTPException as e:
            logger.error(f"Error during self-ping: {e}")

@self_pinger.before_loop
async def before_self_pinger():
    await bot.wait_until_ready()

# HTTP server to control the bot
async def handle_ping(request):
    global bot_running
    action = request.query.get("action", "").lower()
    print(f"Received action: {action}")  # Debugging line

    if action == "stop":
        bot_running["spam"] = False
        spam.stop()
        self_pinger.stop()
        return web.Response(text="Bot tasks stopped.")
    elif action == "start":
        if not spam.is_running():
            spam.start()
        if not self_pinger.is_running():
            self_pinger.start()
        bot_running["spam"] = True
        return web.Response(text="Bot tasks started.")
    else:
        return web.Response(text="Invalid action. Use ?action=start or ?action=stop.")

async def start_http_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP server started on port {port}")

@bot.event
async def on_ready():
    await start_http_server()
    logger.info(f'Logged in as {bot.user.name}')
    if bot_running["spam"]:
        spam.start()
        self_pinger.start()

# Run the bot
bot.run(token)
