import discord
from discord.ext import commands


async def response(ctx: discord.Interaction | commands.Context, *args, **kwargs):
    try:
        if isinstance(ctx, discord.Interaction):
            return await ctx.response.send_message(*args, **kwargs)
        else:
            return await ctx.reply(*args, **kwargs)
    except discord.HTTPException:  # Webhook Token expires after 900 seconds
        return await send(ctx, *args, **kwargs)


async def edit(msg: discord.Message, *args, **kwargs):
    try:
        return await msg.edit(*args, **kwargs)
    except discord.HTTPException:  # Webhook Token expires after 900 seconds
        return await msg.channel.send(*args, **kwargs)


async def send(ctx: discord.Interaction | commands.Context, *args, **kwargs):
    return await ctx.channel.send(*args, **kwargs)
