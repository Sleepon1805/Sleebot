import discord
from discord.ext import commands

from utils import response


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.hybrid_command()
    async def server_info(
        self,
        ctx: commands.Context,
    ):
        """ Prints details of server """
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

        await response(ctx, embed=embed)

    @commands.hybrid_command()
    async def raise_exception(
        self,
        ctx: commands.Context,
        e: str = None
    ):
        """
        Raise and print an exception
        Args:
            ctx: discord ctx object
            e: Error message
        """
        if e is None:
            e = "ManualException"
        await response(ctx, f"Manually raised exception: {e}")
        raise commands.CommandError(e)

    @commands.hybrid_command()
    async def invite_link(
        self,
        ctx: commands.Context,
    ):
        """ Prints the invitation link for the bot """
        link = f"https://discord.com/oauth2/authorize?client_id={self.bot.application_id}"
        await response(ctx, f"Invite me to your server by calling this link:\n {link}")
