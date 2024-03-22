import discord
from discord.ext import commands


async def response(ctx: discord.Interaction | commands.Context, *args, **kwargs):
    if isinstance(ctx, discord.Interaction):
        return await ctx.response.send_message(*args, **kwargs)
    else:
        return await ctx.send(*args, **kwargs)
