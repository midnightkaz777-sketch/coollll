import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# Put the ID of the channel you want to rename here
MEMBER_COUNT_CHANNEL_ID = 1548442322700865650

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    # Start the updater
    if not update_member_count.is_running():
        update_member_count.start()


@tasks.loop(seconds=30)
async def update_member_count():
    for guild in bot.guilds:
        channel = guild.get_channel(MEMBER_COUNT_CHANNEL_ID)

        if channel is None:
            print(f"Could not find the member count channel in {guild.name}")
            continue

        member_count = guild.member_count

        new_name = f"👥・Members: {member_count}"

        if channel.name != new_name:
            try:
                await channel.edit(name=new_name)
                print(f"Updated member count to {member_count}")
            except discord.Forbidden:
                print("I don't have permission to rename this channel.")
            except discord.HTTPException as e:
                print(f"Discord error: {e}")


@update_member_count.before_loop
async def before_update():
    await bot.wait_until_ready()


bot.run(TOKEN)
