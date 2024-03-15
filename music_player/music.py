"""
Source: https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
"""

import discord
from discord.ext.commands import Cog, command

import asyncio

from music_player.player import MusicPlayer


class Music(Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        player = self.players[guild.id]

        queue = player.get_queue_items()
        for source in queue:
            source.empty_cache()

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        guild_id = ctx.guild.id
        if guild_id in self.players:
            player = self.players[guild_id]
        else:
            player = MusicPlayer(ctx)
            self.players[guild_id] = player

        return player

    @command(
        name='connect',
        aliases=['join'],
        brief="Connect to your voice channel.",
    )
    async def connect(self, ctx):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            await ctx.send("Can not connect. You are not connected to any voice channel.")
            return

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                await ctx.send(f'Moving to channel: <{channel}> timed out.')
                return
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                await ctx.send(f'Connecting to channel: <{channel}> timed out.')
                return

        await ctx.send(f'Connected to: **{channel}**', delete_after=20)

    @command(
        name='play',
        aliases=['p', 'sing', 'add'],
        brief="Request a song and add it to the queue.",
        help=
        """
        Request a song and add it to the queue.
        Uses YTDL to automatically search and retrieve a song.
        query: str: A simple search string, an YouTube ID or URL.
        """
    )
    async def play(self, ctx, *, query: str):
        vc = ctx.voice_client
        if not vc:
            await ctx.invoke(self.connect)

        player = self.get_player(ctx)
        await player.add_to_queue(ctx, query)

    @command(
        name='pause',
        brief="Pause the current song",
    )
    async def pause(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: Paused the song!')

    @command(
        name='resume',
        brief="Resume if paused",
    )
    async def resume(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: Resumed the song!')

    @command(
        name='skip',
        brief="Skip the current song",
    )
    async def skip(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: Skipped the song!')

    @command(
        name='queue',
        aliases=['q', 'playlist'],
        brif="Show a queue of upcoming songs",
    )
    async def queue(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('There are currently no more queued songs.')

        # Grab up to 5 entries from the queue...
        upcoming = player.get_queue_items()

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Upcoming songs: {len(upcoming)}', description=fmt)

        await ctx.send(embed=embed)

    @command(
        name='now_playing',
        aliases=['np', 'current', 'currentsong', 'playing'],
        brief="Display information about the current song",
    )
    async def now_playing(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('I am not currently playing anything!')

        try:
            # Remove our previous now_playing message.
            await player.np.delete()
        except discord.HTTPException:
            pass

        player.np = await ctx.send(f'**Now Playing:** `{vc.source.title}` '
                                   f'requested by `{vc.source.requester}`')

    @command(
        name='volume',
        aliases=['v', 'vol'],
        brief="Change the player volume.",
        help=
        """
        Change the player volume.
        volume: float or int: The volume to set the player to in percentage. This must be between 1 and 100.
        """
    )
    async def change_volume(self, ctx, *, volume: float):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        if not 0 < volume < 101:
            return await ctx.send('Please enter a value between 1 and 100.')

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = volume / 100

        player.volume = volume / 100
        await ctx.send(f'**`{ctx.author}`**: Set the volume to **{volume}%**')

    @command(
        name='stop',
        brief="Stop the currently playing song and destroy the player",
    )
    async def stop(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)

        await self.cleanup(ctx.guild)