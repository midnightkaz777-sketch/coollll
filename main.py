import discord
from discord.ext import commands, tasks
import os
import json
import feedparser
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# =========================================================
# CONFIG
# =========================================================

# Member count channel
MEMBER_COUNT_CHANNEL_ID = 1548442322700865650

# YouTube announcement channel
YOUTUBE_ANNOUNCEMENT_CHANNEL_ID = 1548736879166496778

# Your YouTube channel ID
YOUTUBE_CHANNEL_ID = "UCYh_ZzS1LvM0NoFToKlJfZQ"

# How often to check YouTube
YOUTUBE_CHECK_SECONDS = 60

# File used to remember the last posted video
LAST_VIDEO_FILE = "last_youtube_video.json"


# =========================================================
# DISCORD SETUP
# =========================================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# YOUTUBE FUNCTIONS
# =========================================================

def get_last_video_id():
    if not os.path.exists(LAST_VIDEO_FILE):
        return None

    try:
        with open(LAST_VIDEO_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("video_id")

    except Exception:
        return None


def save_last_video_id(video_id):
    with open(LAST_VIDEO_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"video_id": video_id},
            file,
            indent=4
        )


def get_latest_youtube_video():
    feed_url = (
        "https://www.youtube.com/feeds/videos.xml"
        f"?channel_id={YOUTUBE_CHANNEL_ID}"
    )

    feed = feedparser.parse(feed_url)

    if not feed.entries:
        return None

    video = feed.entries[0]

    video_id = video.get("yt_videoid")
    title = video.get("title", "New YouTube Video")
    description = video.get("summary", "")
    video_url = video.get(
        "link",
        f"https://www.youtube.com/watch?v={video_id}"
    )

    thumbnail = (
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    )

    return {
        "id": video_id,
        "title": title,
        "description": description,
        "url": video_url,
        "thumbnail": thumbnail
    }


# =========================================================
# MEMBER COUNT
# =========================================================

@tasks.loop(seconds=30)
async def update_member_count():

    for guild in bot.guilds:

        channel = guild.get_channel(
            MEMBER_COUNT_CHANNEL_ID
        )

        if channel is None:
            print(
                f"Could not find member count channel "
                f"in {guild.name}"
            )
            continue

        member_count = guild.member_count

        new_name = f"👥・Members: {member_count}"

        if channel.name == new_name:
            continue

        try:
            await channel.edit(name=new_name)

            print(
                f"[{guild.name}] "
                f"Updated member count to {member_count}"
            )

        except discord.Forbidden:
            print(
                f"[{guild.name}] "
                "I don't have permission to rename "
                "the member count channel."
            )

        except discord.HTTPException as e:
            print(
                f"[{guild.name}] Discord error: {e}"
            )


@update_member_count.before_loop
async def before_member_count_update():
    await bot.wait_until_ready()


# =========================================================
# YOUTUBE AUTO POST
# =========================================================

@tasks.loop(seconds=YOUTUBE_CHECK_SECONDS)
async def check_youtube():

    channel = bot.get_channel(
        YOUTUBE_ANNOUNCEMENT_CHANNEL_ID
    )

    if channel is None:
        print(
            "Could not find the YouTube announcement channel."
        )
        return

    try:
        video = get_latest_youtube_video()

        if video is None:
            print("Could not find a YouTube video.")
            return

        latest_video_id = video["id"]
        last_video_id = get_last_video_id()

        # First startup
        #
        # Save the current video without posting it.
        # This prevents the bot from posting an old video
        # when it first starts.
        if last_video_id is None:
            save_last_video_id(latest_video_id)

            print(
                "YouTube tracker initialized with:"
                f" {video['title']}"
            )

            return

        # Already posted
        if latest_video_id == last_video_id:
            return

        # -------------------------------------------------
        # CREATE EMBED
        # -------------------------------------------------

        embed = discord.Embed(
            title="🎬 New YouTube Video!",
            description=(
                f"**{video['title']}**\n\n"
                "A new video has just been uploaded!"
            ),
            url=video["url"],
            color=discord.Color.red()
        )

        embed.set_author(
            name="New upload from Kaz",
            url=(
                "https://www.youtube.com/channel/"
                f"{YOUTUBE_CHANNEL_ID}"
            )
        )

        embed.set_thumbnail(
            url=video["thumbnail"]
        )

        embed.add_field(
            name="▶️ Watch the Video",
            value="Click the button below to watch it.",
            inline=False
        )

        embed.set_footer(
            text="Thanks for watching! ❤️"
        )

        # -------------------------------------------------
        # BUTTONS
        # -------------------------------------------------

        view = discord.ui.View()

        watch_button = discord.ui.Button(
            label="Watch Video",
            emoji="▶️",
            style=discord.ButtonStyle.link,
            url=video["url"]
        )

        channel_button = discord.ui.Button(
            label="YouTube Channel",
            emoji="📺",
            style=discord.ButtonStyle.link,
            url=(
                "https://www.youtube.com/channel/"
                f"{YOUTUBE_CHANNEL_ID}"
            )
        )

        view.add_item(watch_button)
        view.add_item(channel_button)

        # -------------------------------------------------
        # SEND MESSAGE
        # -------------------------------------------------

        await channel.send(
            embed=embed,
            view=view
        )

        # Save only after successfully posting
        save_last_video_id(latest_video_id)

        print(
            f"📺 Posted new YouTube video: "
            f"{video['title']}"
        )

    except Exception as e:
        print(
            f"YouTube checker error: {e}"
        )


@check_youtube.before_loop
async def before_youtube_check():
    await bot.wait_until_ready()


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    print("=" * 50)
    print(f"Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")
    print("=" * 50)

    if not update_member_count.is_running():
        update_member_count.start()

    if not check_youtube.is_running():
        check_youtube.start()


# =========================================================
# TOKEN CHECK
# =========================================================

if not TOKEN:
    raise ValueError(
        "TOKEN is missing from your environment variables."
    )


# =========================================================
# START BOT
# =========================================================

bot.run(TOKEN)
