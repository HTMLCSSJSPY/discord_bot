import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))

# Logging setup
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Swear words list
swear_words = ("shit", "fuck", "crap", "bitch")

# Discord Bot class
class MyBot(commands.Bot):
    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Slash commands synced.")

bot = MyBot(command_prefix="/", intents=intents)

# Function to get YouTube subscriber count
def get_subscriber_count():
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.channels().list(
            part='statistics',
            id=YOUTUBE_CHANNEL_ID
        )
        response = request.execute()
        return response['items'][0]['statistics']['subscriberCount']
    except Exception as e:
        logging.error(f"Error fetching subscriber count: {e}")
        return "N/A"

# Task to update subscriber count every 60 seconds
@tasks.loop(seconds=1800)
async def update_subscriber_count():
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        logging.error("Could not find the target channel.")
        return
    subs = get_subscriber_count()
    await channel.send(f"Current YouTube Subscribers: {subs}")

@bot.event
async def on_ready():
    print(f"We are ready to run as {bot.user}!")
    if not update_subscriber_count.is_running():
        update_subscriber_count.start()

@bot.event
async def on_member_join(member):
    try:
        await member.send(f"Glad you dropped in {member.name}")
    except Exception as e:
        logging.warning(f"Could not send welcome DM to {member.name}: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Swear word filter
    if any(word in message.content.lower() for word in swear_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention} - don't use that word!")
        return

    # Simple hello response
    if "hello" in message.content.lower():
        await message.channel.send(f"Hello {message.author.mention}!")

    await bot.process_commands(message)

# Slash command example
@bot.tree.command(name="eval")
async def eval_command(interaction: discord.Interaction):
    print("Working")
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

bot.run(DISCORD_TOKEN, log_handler=handler, log_level=logging.DEBUG)
