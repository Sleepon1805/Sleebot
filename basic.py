import discord
from discord.ext import commands


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='server_info',
        brief="Prints details of server",
    )
    async def server_info(self, ctx):
        guild_name = ctx.guild.name
        owner = str(ctx.guild.owner)
        region = str(ctx.guild.region) if hasattr(ctx.guild, "region") else ""
        guild_id = str(ctx.guild.id)
        memberCount = str(ctx.guild.member_count)
        icon = str(ctx.guild.icon_url) if hasattr(ctx.guild, "icon_url") else None
        desc = ctx.guild.description if hasattr(ctx.guild, "description") else ""

        embed = discord.Embed(
            title=guild_name,
            description=desc,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=icon)
        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Region", value=region, inline=True)
        embed.add_field(name="Server ID", value=guild_id, inline=True)
        embed.add_field(name="Member Count", value=memberCount, inline=True)

        await ctx.send(embed=embed)

    @commands.command(
        name='hello',
        brief="Introduces Sleebot",
    )
    async def hello(self, ctx):
        text = "Hello! My name is Sleebot! Contact @Sleepon for any questions."
        await ctx.send(text)

    @commands.command(
        name='pm',
        brief="Sends a message to your personal messages",
    )
    async def pm(self, ctx):
        await ctx.author.send('Hello! Type !help to get list of available commands.')

    @commands.command(
        name='raise_exception',
        aliases=['raise'],
        brief="Prints and raises an exception",
        hidden=True,
    )
    async def raise_exception(self, ctx, msg: str = None):
        if msg is None:
            msg = "Manually raised Exception"
        raise commands.CommandError(msg)
