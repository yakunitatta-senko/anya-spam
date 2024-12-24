import os
import random
import string
import asyncio
import logging
import discord
from discord.ext import commands, tasks
from aiohttp import web
from dotenv import load_dotenv

# Install discord.py-self if not already installed
os.system('pip install discord.py-self && pip install --upgrade pip')

# Create a bot instance with sharding (manual control)
bot = commands.Bot(command_prefix="!", help_command=None, self_bot=True)
bot.channel = None

# Load environment variables
load_dotenv()
token = os.getenv("TOKEN")

# Maximum messages before stopping
MAX_MESSAGES = 150

# Message counter
message_count = 0

# Task to spam messages with random intervals and incremental delay
@tasks.loop(seconds=3)
async def spam():
    global message_count
    if bot.channel is None:
        bot.channel = bot.get_channel(1278580578593148978)  # Replace with your channel ID

    if bot.channel is not None:
        try:
            if message_count >= MAX_MESSAGES:
                print(f"Reached the message limit of {MAX_MESSAGES}. Stopping the spam task.")
                spam.stop()  # Stop the spam task
                return

            # Generate random text
            text = ''.join(random.sample(string.ascii_letters + string.digits, 40))

            # Send the message
            await bot.channel.send(text)
            print(f"Sent message: {text}")

            # Increment the counter
            message_count += 1

            # Random cooldown to simulate varying delay
            cooldown = random.uniform(1, 3)  # Cooldown between 1 and 3 seconds
            await asyncio.sleep(cooldown)

        except discord.HTTPException as e:
            print(f"Failed to send message due to rate limit or server error: {e}")

@spam.before_loop
async def before_spam():
    await bot.wait_until_ready()

# Task for self-pinging to keep the bot alive
@tasks.loop(seconds=60)
async def self_pinger():
    try:
        if bot.channel is not None:
            await bot.channel.send("Pong!")
    except discord.HTTPException as e:
        print(f"Error during self-ping: {e}")

@self_pinger.before_loop
async def before_self_pinger():
    await bot.wait_until_ready()

async def start_http_server():
    try:
        app = web.Application()

        # HTTP route to restart the spam task
        async def restart_spam(request):
            global message_count
            if not spam.is_running():
                message_count = 0  # Reset the counter
                spam.start()  # Restart the spam task
                return web.Response(text="Spam task restarted.")
            return web.Response(text="Spam task is already running.")

        app.router.add_get('/', lambda request: web.Response(text="Bot is running"))
        app.router.add_post('/restart', restart_spam)

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"HTTP server started on port {port}")
    except Exception as e:
        logging.error(f"Failed to start HTTP server: {e}")
        print("Failed to start HTTP server.")

@bot.event
async def on_ready():
    await start_http_server()
    print(f'Logged in as {bot.user.name}')
    spam.start()  # Start the spam task when the bot is ready
    self_pinger.start()  # Start the self-pinger to keep the bot alive

bot.run(token)
