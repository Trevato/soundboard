import discord
import asyncio

from discord.ext import commands
from db_connector import (
    connect,
    list_sounds,
    create_yt_sound,
    create_mp3_sound,
    get_url,
    delete_sound,
)
from audio_handler import YTDLSource


class Soundboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = connect()

    # Create the help command
    # Shows the user how to interact with the bot
    @commands.command()
    async def h(self, ctx):
        # Send a message to the current context
        # Message is formatted using markdown to look pretty in the discord front end
        await ctx.send(
            """```!new <sound name> <url>  Creates a new sound\n!play <sound name>       Plays a sound\n!delete <sound name>     Deletes a sound\n!list                    Lists your sounds```"""
        )

    # Create the list command
    # Lists all the sounds the user has created
    @commands.command()
    async def list(self, ctx):
        response = "```"
        for sound in list_sounds(ctx, self.conn):
            response += str(sound[2] + "\n")

        await ctx.send(response + "```")

        # Log the interaction
        self.logger.info(f"{ctx.author} requested a list of their sounds")

    # Create the new command
    # Stores a new sound for the user
    @commands.command()
    async def new(self, ctx):
        # The new command has two control flows.
        # The first will handle if the user has passed a YouTube link
        # The second will handle if the user passed a file

        response = "Successfully created new sound!"

        if len(ctx.message.content.split()) == 3:
            response = create_yt_sound(ctx, self.conn)

        elif len(ctx.message.content.split()) == 2:
            response = create_mp3_sound(ctx, self.conn)

        await ctx.send(response)

    # Create the play command
    # Bot will enter the voice channel that the user is currently in and play the audio
    @commands.command()
    async def play(self, ctx):
        if len(ctx.message.content.split()) != 2:
            await ctx.send("```Usage: !play <sound name>```")
            return

        sound_path = get_url(ctx, self.conn)

        # Set the bot to typing to give the user assurance that something is happening
        async with ctx.typing():
            # Ensure we aren't already in a voice channel
            if ctx.voice_client is None:
                # TODO: Looping here is annoying. Perhaps we can eventually get user permissions and don't need to search.
                # Loop through mutual servers
                for guild in ctx.author.mutual_guilds:
                    # Loop through each servers' voice channels
                    for channel in guild.voice_channels:
                        # Check if the user is in this channel
                        if ctx.author in channel.members:
                            # Connect to this channel
                            voice = await channel.connect()

                            # Get an instance of the audio player
                            player = await YTDLSource.from_url(
                                sound_path, loop=bot.loop, stream=True
                            )

                            # Play the audio through the voice channel
                            voice.play(
                                player,
                                after=lambda e: print(f"Player error: {e}")
                                if e
                                else None,
                            )

                            # Tell the user that their sound is playing
                            await ctx.send(f"Now playing: {player.title}")

                            # Check if the player is still playing
                            # TODO: This is gross. Tried disconnecting in the play `after` argument but it gets weird
                            while voice.is_playing():
                                await asyncio.sleep(1)

                            await voice.disconnect()
                            return

    # Create delete command
    # Deletes a sound that the user has registered
    @commands.command()
    async def delete(self, ctx):
        if len(ctx.message.content.split()) != 2:
            await ctx.send("```Usage: !delete <sound name>```")

        await ctx.send(delete_sound(ctx, self.conn))


# Declare Discord intents
intents = discord.Intents.default()
intents.message_content = True

# Create the bot
bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("!"),
    description="Create your own soundboard to use on any supported server!",
    intents=intents,
)

# When bot is ready, adjust the apperance
# Here we change the presence to show the user how to get help
@bot.event
async def on_ready():
    # Set the bot's status
    # TODO: Look at the discord documentation to see if we can get a better looking presence
    await bot.change_presence(activity=discord.Game(name="!h for help"))

    print("Bot is ready!")


async def main():
    async with bot:
        # Add the soundboard cog
        await bot.add_cog(Soundboard(bot))
        # Get the token from the token.txt file
        with open("token.txt", "r") as f:
            await bot.start(f.read())


asyncio.run(main())
