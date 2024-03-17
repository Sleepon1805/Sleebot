"""
Source: https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
"""
import asyncio
from discord.ext.commands import Cog, command

from music_player.player import MusicPlayer
from music_player.spotify_search import SpotifyHandler


class Music(Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

        self.spotify_handler = SpotifyHandler()

    def get_player(self, ctx) -> MusicPlayer:
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
        brief="Connects to your voice channel.",
        hidden=True,
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
        brief="(Youtube) Requests a song by query or URL",
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
        await player.send_new_embed_msg(ctx)
        await player.add_to_queue(ctx, query)

    @command(
        name='artist',
        brief="(Spotify) Requests a top songs from artist",
        help=
        """
        Requests a top songs from artist based on spotify search.
        Uses YTDL to automatically search and retrieve a song.
        artist_name: str: An artist name.
        limit: int: The number of top songs to add to the queue.
        """
    )
    async def artist(self, ctx, *args):
        if args[-1].isdigit():
            artist_name = ' '.join(args[:-1])
            limit = int(args[-1])
        else:
            artist_name = ' '.join(args)
            limit = None

        vc = ctx.voice_client
        if not vc:
            await ctx.invoke(self.connect)

        top_tracks = self.spotify_handler.get_artist_top_tracks(
            artist_name, limit=limit, return_search=True)  # YouTube search queries

        player = self.get_player(ctx)
        await player.send_new_embed_msg(ctx)
        await player.add_to_queue(ctx, top_tracks)

    @command(
        name='mix',
        aliases=['jam'],
        brief="(Spotify) Requests a mix playlist by artist (n songs)",
        help=
        """
        Requests a songs from Mix-Playlist by Spotify.
        Uses YTDL to automatically search and retrieve a song.
        artist_name: str: An artist name.
        limit: int: The number of top songs to add to the queue.
        """
    )
    async def mix(self, ctx, *args):
        if args[-1].isdigit():
            artist_name = ' '.join(args[:-1])
            limit = int(args[-1])
        else:
            artist_name = ' '.join(args)
            limit = None

        vc = ctx.voice_client
        if not vc:
            await ctx.invoke(self.connect)

        top_tracks = self.spotify_handler.get_artist_mix(
            artist_name, limit=limit, return_search=True)  # YouTube search queries

        player = self.get_player(ctx)
        await player.send_new_embed_msg(ctx)
        await player.add_to_queue(ctx, top_tracks)

    @command(
        name='recs',
        aliases=['r', 'rec', 'recommendations'],
        brief="(Spotify) Requests a spotify recommendations by artist",
        help=
        """
        Requests songs from spotify recommendations based on artist seed.
        Uses YTDL to automatically search and retrieve a song.
        artist_name: str: An artist name.
        limit: int: The number of top songs to add to the queue.
        """
    )
    async def recs(self, ctx, *args):
        if args[-1].isdigit():
            artist_name = ' '.join(args[:-1])
            limit = int(args[-1])
        else:
            artist_name = ' '.join(args)
            limit = None

        vc = ctx.voice_client
        if not vc:
            await ctx.invoke(self.connect)

        top_tracks = self.spotify_handler.get_artist_recommendations(
            artist_name, limit=limit, return_search=True)  # YouTube search queries

        player = self.get_player(ctx)
        await player.send_new_embed_msg(ctx)
        await player.add_to_queue(ctx, top_tracks)

    @command(
        name='pause',
        brief="Pauses the current song",
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
        brief="Resumes if paused",
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
        brief="Skips the current song",
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
        name='stop',
        brief="Stops and empties the queue.",
    )
    async def stop(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)

        player = self.players.pop(ctx.guild.id, None)
        if player:
            await player.destroy()

    @command(
        name='queue',
        aliases=['q', 's', 'np', 'status', 'playing', 'now_playing'],
        brief="Shows a queue of upcoming songs",
    )
    async def queue(self, ctx):
        player = self.get_player(ctx)
        await player.send_new_embed_msg(ctx)

    @command(
        name='shuffle',
        brief="Shuffles a queue of upcoming songs",
    )
    async def shuffle(self, ctx):
        player = self.get_player(ctx)
        player.shuffle_queue()
        await player.send_new_embed_msg(ctx)

    @command(
        name='volume',
        aliases=['v', 'vol'],
        brief="Changes the player volume.",
        help=
        """
        Changes the player volume
        volume: float or int: The volume to set the player to in percentage. This must be between 1 and 100.
        """
    )
    async def change_volume(self, ctx, *, volume: float):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        if not 1 <= volume <= 100:
            return await ctx.send('Please enter a value between 1 and 100.')

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = volume / 100

        player.volume = volume / 100
        await ctx.send(f'**`{ctx.author}`**: Set the volume to **{volume}%**')
