import discord
from discord.ext import commands, tasks

from utils import response, edit, send


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

    @commands.hybrid_command()
    async def timer(
        self,
        ctx: commands.Context,
        seconds: int,
        event_name: str = None
    ):
        """
        Start a timer
        Args:
            ctx: discord ctx object
            seconds: Number of seconds to count down
            event_name: Name of the event to count down to
        """
        timer_name = f"Timer till {event_name}" if event_name else "Timer"
        await response(ctx, f"Starting {timer_name} ({seconds} sec)")
        message = await send(ctx, f"Starting {timer_name} ({seconds} sec)")

        @tasks.loop(seconds=1, count=seconds)
        async def timer_loop():
            await edit(message, content=f"{timer_name}: {seconds - timer_loop.current_loop}")

        await timer_loop.start()
        await edit(message, content=f"{event_name} has started!" if event_name else "Timer has ended")

    @discord.app_commands.command(name='help')
    async def help_msg(self, interaction: discord.Interaction):
        """
        Show help menu
        """
        embed = discord.Embed(
            title=f'Help Menu',
            description='If you want to run a command with "!" and multiple arguments, you can use\n'
                        '```!<command_name> "<arg1>" "<arg2>" "<arg3>"```',
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(
            url=self.bot.user.avatar.url
        )

        for ind, slash_command in enumerate(self.bot.tree.walk_commands()):
            if isinstance(slash_command, commands.hybrid.HybridAppCommand):
                name = f"/{slash_command.name} | !{slash_command.name}"
            else:
                name = slash_command.name
            description = slash_command.description if slash_command.description else slash_command.name
            for p in slash_command.parameters:
                description += f"\n> {p.display_name} ({p.type.name}): {p.description}"
            embed.add_field(name=f"{ind}. {name}",
                            value=description,
                            inline=False)

        await response(interaction, embed=embed)
