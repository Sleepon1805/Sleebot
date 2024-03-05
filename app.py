import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands

from music import Music
from basic import Basic


def run_discord_bot():
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

        await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=" Music, type !help "))

    @bot.event
    async def on_command_error(ctx, error):
        await ctx.send(error)

    return bot


async def main():
    load_dotenv()
    DISCORD_TOKEN = os.getenv("discord_token")

    bot = run_discord_bot()

    async with bot:
        await bot.add_cog(Basic(bot))
        await bot.add_cog(Music(bot))
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
