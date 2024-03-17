import os
import asyncio
import logging
import logging.handlers
from dotenv import load_dotenv
import discord
from discord.ext import commands

from basic import Basic
from music_player.music import Music


def setup_logging():
    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    formatter = logging.Formatter(
        fmt='[{levelname:<8}] {asctime} | {message}',
        datefmt='%d-%m-%Y %H:%M:%S',
        style='{'
    )
    handler.setFormatter(formatter)
    discord.utils.setup_logging(level=logging.WARNING, handler=handler, formatter=formatter, root=True)


async def run_discord_bot():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix='!',
        intents=intents,
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="!help"
        )
    )

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
        print(f"discord lib version: {discord.__version__}")
        print('------')
        print('Servers connected to:')
        for guild in bot.guilds:
            print(f"{guild.name} (ID: {guild.id})")
        print('------')

    @bot.event
    async def on_guild_join(guild):
        print(f"Joined guild {guild.name}")

    @bot.event
    async def on_command_error(ctx, error):
        logging.error(error)
        await ctx.send(error)

    @bot.before_invoke
    async def before_invoke(ctx):
        msg = f"Received command: {ctx.message.content} from {ctx.author.name} in {ctx.guild.name}"
        logging.warning(msg)

    load_dotenv()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    async with bot:
        await bot.add_cog(Basic(bot))
        await bot.add_cog(Music(bot))
        await bot.start(DISCORD_TOKEN)

    return bot

if __name__ == "__main__":
    setup_logging()
    asyncio.run(run_discord_bot())
