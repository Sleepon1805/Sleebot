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
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


async def run_discord_bot():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
        print(f"discord lib version: {discord.__version__}")
        print('------')
        print('Servers connected to:')
        for guild in bot.guilds:
            print(f"{guild.name} (ID: {guild.id})")
        print('------')

        # await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=" Music, type !help "))

    @bot.event
    async def on_guild_join(guild):
        print(f"Joined guild {guild.name}")

    @bot.event
    async def on_command_error(ctx, error):
        print(error)
        await ctx.send(error)

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
