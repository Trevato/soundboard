import discord
import asyncio
import youtube_dl

import sqlite3 as sl

from discord.ext import commands


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""


ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    "options": "-vn",
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Soundboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Create the new command to add a sound
    @commands.command()
    async def new(self, ctx):
        # Check that the message is private
        if ctx.guild is not None:
            return

        # Check that the message has 3 arguments
        if len(ctx.message.content.split()) != 3:
            # Send a message to the user
            await ctx.send("Usage: !new <sound name> <url>")
            return

        if "/shorts/" in ctx.message.content.split()[2]:
            await ctx.send("Shorts are not supported")
            return

        if "?t=" in ctx.message.content.split()[2]:
            await ctx.send("Start times are not supported")
            return

        # Check that the message has a valid youtube url
        if not ctx.message.content.split()[2].startswith(
            "https://youtu.be/"
        ) and not ctx.message.content.split()[2].startswith("https://www.youtube.com/"):
            # Send a message to the user
            await ctx.send("Invalid youtube url")
            return

        # Get the sound name and url
        sound_name = ctx.message.content.split()[1]
        sound_path = ctx.message.content.split()[2]

        # Get the user id
        user_id = ctx.author.id

        # Check if the user already has a sound with that name
        c = conn.cursor()
        c.execute(
            "SELECT * FROM sounds WHERE user_id = ? AND sound_name = ?",
            (user_id, sound_name),
        )
        if c.fetchone() is not None:
            await ctx.send("You already have a sound with that name")
            return

        # Insert the sound into the database
        c.execute(
            "INSERT INTO sounds (user_id, sound_name, sound_path) VALUES (?, ?, ?)",
            (user_id, sound_name, sound_path),
        )
        conn.commit()

        # Send a message to the user
        await ctx.send("Sound added!")

    # Create the new command to play a sound
    @commands.command()
    async def play(self, ctx, *, name):
        # Check that the message is private
        if ctx.guild is not None:
            # Send a message to the user
            await ctx.send("This command can only be used in private messages")
            return

        # Check that the message has 2 arguments
        if len(ctx.message.content.split()) != 2:
            # Send a message to the user
            await ctx.send("Usage: !play <sound name>")
            return

        # Get the user id
        user_id = ctx.author.id

        # Check if the user has a sound with that name
        c = conn.cursor()
        c.execute(
            "SELECT * FROM sounds WHERE user_id = ? AND sound_name = ?", (user_id, name)
        )
        if c.fetchone() is None:
            await ctx.send("You don't have a sound with that name")
            return

        # Get the url of the sound
        c.execute(
            "SELECT sound_path FROM sounds WHERE user_id = ? AND sound_name = ?",
            (user_id, name),
        )
        sound_path = c.fetchone()[0]

        # Check that the user and the bot are in a mutual voice channel
        if not ctx.author.mutual_guilds:
            await ctx.send("We don't share a mutual server")
            return

        async with ctx.typing():
            if ctx.voice_client is None:
                for guild in ctx.author.mutual_guilds:
                    for channel in guild.voice_channels:
                        if ctx.author in channel.members:
                            voice = await channel.connect()

                            player = await YTDLSource.from_url(
                                sound_path, loop=bot.loop, stream=True
                            )
                            print("starting player")
                            voice.play(
                                player,
                                after=lambda e: print(f"Player error: {e}")
                                if e
                                else None,
                            )
                            print("playing")
                            await ctx.send(f"Now playing: {player.title}")

                            # Check if the player is still playing
                            while voice.is_playing():
                                await asyncio.sleep(1)

                            await voice.disconnect()
                            return

    # Delete command to delete a sound
    @commands.command()
    async def delete(self, ctx, *, name):
        # Check that the message is private
        if ctx.guild is not None:
            # Send a message to the user
            await ctx.send("This command can only be used in private messages")
            return

        # Check that the message has 2 arguments
        if len(ctx.message.content.split()) != 2:
            # Send a message to the user
            await ctx.send("Usage: !delete <sound name>")
            return

        # Get the user id
        user_id = ctx.author.id

        # Check if the user has a sound with that name
        c = conn.cursor()
        c.execute(
            "SELECT * FROM sounds WHERE user_id = ? AND sound_name = ?", (user_id, name)
        )
        if c.fetchone() is None:
            await ctx.send("You don't have a sound with that name")
            return

        # Delete the sound from the database
        c.execute(
            "DELETE FROM sounds WHERE user_id = ? AND sound_name = ?", (user_id, name)
        )
        conn.commit()

        # Send a message to the user
        await ctx.send("Sound deleted!")

    # List command to list all the sounds
    @commands.command()
    async def list(self, ctx):
        # Check that the message is private
        if ctx.guild is not None:
            # Send a message to the user
            await ctx.send("This command can only be used in private messages")
            return

        # Get the user id
        user_id = ctx.author.id

        # Get all the sounds from the database
        c = conn.cursor()
        c.execute("SELECT sound_name FROM sounds WHERE user_id = ?", (user_id,))
        sounds = c.fetchall()

        # Create a string with all the sound names
        sound_names = "```"
        for sound in sounds:
            sound_names += sound[0] + "\n"

        # Send a message to the user
        await ctx.send(sound_names + "```")

    # Create the help command
    @commands.command()
    async def h(self, ctx):
        # Check that the message is private
        if ctx.guild is not None:
            # Send a message to the user
            await ctx.send("This command can only be used in private messages")
            return

        # Send a message to the user
        await ctx.send(
            "```!new <sound name> <url> - Creates a new sound\n!play <sound name> - Plays a sound\n!delete <sound name> - Deletes a sound\n!list - Lists all the sounds```"
        )


print("Connecting to database...")
conn = sl.connect("database.db")
print("Connected to database!")

# create the table if it doesn't exist
# Schema: (id, use_id, sound_name, sound_path)
conn.execute(
    "CREATE TABLE IF NOT EXISTS sounds (id INTEGER PRIMARY KEY, user_id INTEGER, sound_name TEXT, sound_path TEXT)"
)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("!"),
    description="Relatively simple music bot example",
    intents=intents,
)


@bot.event
async def on_ready():
    # Set the bot's status
    await bot.change_presence(activity=discord.Game(name="!h for help"))


async def main():
    async with bot:
        await bot.add_cog(Soundboard(bot))
        # Get the token from the token.txt file
        with open("token.txt", "r") as f:
            await bot.start(f.read())


asyncio.run(main())
