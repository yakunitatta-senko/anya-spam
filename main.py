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

# Create a bot instance
bot = commands.Bot(command_prefix="!", help_command=None, self_bot=True)
bot.channel = None

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared state for bot task control
bot_running = {"spam": True}

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

# HTTP server to toggle tasks on any ping
async def handle_ping(request):
    global bot_running

    # Toggle the spam task
    bot_running["spam"] = not bot_running["spam"]
    if bot_running["spam"]:
        if not spam.is_running():
            spam.start()
        logger.info("Bot tasks started.")
        return web.Response(text="Bot tasks started.")
    else:
        if spam.is_running():
            spam.stop()
        logger.info("Bot tasks stopped.")
        return web.Response(text="Bot tasks stopped.")

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

# Run the bot
bot.run(token)
