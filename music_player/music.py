"""
Source: https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
"""
import asyncio
import discord
from discord.ext import commands
from typing import Literal, Optional, Dict, List

from music_player.player import MusicPlayer
from music_player.spotify_search import SpotifyHandler
from music_player.track import Track
from utils import response


class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players: Dict[int, MusicPlayer] = {}

        self.spotify_handler = SpotifyHandler()

    @staticmethod
    def get_voice_client(ctx: commands.Context) -> discord.VoiceClient | None:
        return ctx.voice_client

    def get_player(self, ctx: commands.Context) -> MusicPlayer:
        """
        Retrieve the guild player, or generate one.
        """
        guild_id = ctx.guild.id
        if guild_id in self.players:
            player = self.players[guild_id]
        else:
            player = MusicPlayer(self.bot, self.get_voice_client(ctx))
            self.players[guild_id] = player

        return player

    async def connect(self, ctx: commands.Context) -> Optional[str]:
        """
        Connect to requester voice channel.
        """
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            msg = "Can not connect. You are not connected to any voice channel."
            return msg

        vc = self.get_voice_client(ctx)

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                msg = f'Moving to channel: <{channel}> timed out.'
                return msg
        else:
            try:
                await channel.connect()
                return
            except asyncio.TimeoutError:
                msg = f'Connecting to channel: <{channel}> timed out.'
                return msg

    async def start_player(self, ctx: commands.Context) -> MusicPlayer:
        msg = await self.connect(ctx)
        if msg:
            await response(ctx, msg)

        player = self.get_player(ctx)
        await player.send_new_embed_msg(ctx)
        return player

    @commands.hybrid_command(aliases=['p', 'yt', 'youtube'])
    async def play(
        self,
        ctx: commands.Context,
        query: str
    ):
        """
        Request a song by YouTube search or URL.
        Args:
            ctx: discord Context object
            query: Search query or YouTube URL (video or playlist)
        """
        player = await self.start_player(ctx)

        if "youtube.com" in query or "youtu.be" in query:
            if "playlist?list=" in query:
                tracks = await Track.from_playlist(playlist_url=query, requester=ctx.author, loop=self.bot.loop)
            else:
                tracks = [await Track.from_url(url=query, requester=ctx.author, loop=self.bot.loop)]
        else:
            tracks = [await Track.from_search(query=query, requester=ctx.author, loop=self.bot.loop)]

        await player.add_to_queue(ctx, tracks)

    @commands.hybrid_command()
    async def spotify(
        self,
        ctx: commands.Context,
        category: Literal["track", "artist", "album", "playlist", "link"],
        search: str,
        limit: int = None
    ):
        """
        Make a spotify search and add YT songs to the queue.
        Args:
            ctx: discord Context object
            category: Category to search for
            search: Search query or URL. Only exact search matches are processed.
            limit: Numer of songs to add to the queue
        """
        player = await self.start_player(ctx)

        if category == 'link':
            item, out_msg = self.spotify_handler.process_url(search)
        else:
            item, out_msg = self.spotify_handler.process_search(search, category)

        if item is None:
            await response(ctx, out_msg)
            return

        category = item['type']
        tracks = self.spotify_handler.get_tracks_from_spotify_object(
            item, category, ctx, limit=limit, get_recommendations=False)

        await player.add_to_queue(ctx, tracks)

    @commands.hybrid_command()
    async def recs(
        self,
        ctx: commands.Context,
        category: Literal["track", "artist", "album", "playlist", "link"],
        search: str,
        limit: int = None
    ):
        """
        Get spotify recommendations based on a spotify search and add YT songs to the queue.
        Args:
            ctx: discord Context object
            category: Category to search for
            search: Search query or URL. Only exact search matches are processed.
            limit: Numer of songs to add to the queue
        """
        player = await self.start_player(ctx)

        if category == 'link':
            item, out_msg = self.spotify_handler.process_url(search)
        else:
            item, out_msg = self.spotify_handler.process_search(search, category)

        if item is None:
            await response(ctx, out_msg)
            return

        category = item['type']
        tracks = self.spotify_handler.get_tracks_from_spotify_object(
            item, category, ctx, limit=limit, get_recommendations=True)

        await player.add_to_queue(ctx, tracks)

    @commands.hybrid_command()
    async def pause(
        self,
        ctx: commands.Context,
    ):
        """
        Pause the current song.
        Args:
            ctx: discord Context object
        """
        vc = self.get_voice_client(ctx)

        if not vc or not vc.is_playing():
            await response(ctx, 'I am not currently playing anything!')
        elif not vc.is_paused():
            vc.pause()
            await response(ctx, f'**`{ctx.author}`**: Paused the song')

    @commands.hybrid_command()
    async def resume(
        self,
        ctx: commands.Context,
    ):
        """
        Resume if paused.
        Args:
            ctx: discord Context object
        """
        vc = self.get_voice_client(ctx)

        if not vc or not vc.is_connected():
            await response(ctx, 'I am not currently playing anything!')
        elif vc.is_paused():
            vc.resume()
            await response(ctx, f'**`{ctx.author}`**: Resumed the song')

    @commands.hybrid_command()
    async def skip(
        self,
        ctx: commands.Context,
    ):
        """
        Skip the current song.
        Args:
            ctx: discord Context object
        """
        vc = self.get_voice_client(ctx)

        if not vc or not vc.is_connected():
            await response(ctx, 'I am not currently playing anything!')
        else:
            vc.stop()
            await response(ctx, f'**`{ctx.author}`**: Skipped the song')

    @commands.hybrid_command()
    async def stop(
        self,
        ctx: commands.Context,
    ):
        """
        Stop and empty the queue.
        Args:
            ctx: discord Context object
        """
        vc = self.get_voice_client(ctx)

        if not vc or not vc.is_connected():
            await response(ctx, 'I am not currently playing anything!')
        else:
            player = self.players.pop(ctx.guild.id, None)
            if player:
                await player.destroy()
            await response(ctx, f'**`{ctx.author}`**: Stopped player')

    @commands.hybrid_command()
    async def restart(
            self,
            ctx: commands.Context,
    ):
        """
        Save the queue and restart the player
        Args:
            ctx: discord Context object
        """
        player = self.get_player(ctx)
        songs: List[Track] = []
        if player.current:
            songs.append(player.current)
        if len(player.get_queue_items()) > 0:
            songs.extend(player.get_queue_items())

        player = self.players.pop(ctx.guild.id, None)
        if player:
            await player.destroy()

        if len(songs) > 0:
            player = await self.start_player(ctx)
            await player.add_to_queue(ctx, songs)

    @commands.hybrid_command(aliases=['q'])
    async def queue(
        self,
        ctx: commands.Context,
    ):
        """
        Show a queue of upcoming songs.
        Args:
            ctx: discord Context object
        """
        player = self.get_player(ctx)
        await response(ctx, 'Queue:')
        await player.send_new_embed_msg(ctx)

    @commands.hybrid_command()
    async def shuffle(
        self,
        ctx: commands.Context,
    ):
        """
        Shuffle the queue.
        Args:
            ctx: discord Context object
        """
        player = self.get_player(ctx)
        player.shuffle_queue()
        await response(ctx, f'**`{ctx.author}`**: Shuffled the queue')
        await player.send_new_embed_msg(ctx)

    @commands.hybrid_command()
    async def change_volume(
        self,
        ctx: commands.Context,
        volume: float
    ):
        """
        Change the player volume.
        Args:
            ctx: discord Context object
            volume: Percentage value between 1 and 100
        """
        vc = self.get_voice_client(ctx)

        if not vc or not vc.is_connected():
            await response(ctx, 'I am not currently connected to voice!')
        elif not 1 <= volume <= 100:
            await response(ctx, 'Please enter a value between 1 and 100.')
        else:
            player = self.get_player(ctx)

            if vc.source:
                vc.source.volume = volume / 100

            player.volume = volume / 100
            await response(ctx, f'**`{ctx.author}`**: Set the volume to **{volume}%**')

    @commands.hybrid_command()
    async def status(
        self,
        ctx: commands.Context
    ):
        """
        Prints some status information
        Args:
            ctx: discord ctx object
        """
        msg = ''
        msg += f"Current guild is {ctx.guild}\n"
        msg += f"Current channel is {ctx.channel}\n"
        msg += f"Current voice client is {ctx.voice_client}\n"

        player = self.get_player(ctx)
        if player:
            msg += f"Current player is {player}\n"
            msg += f"Current queue is {[item.title for item in player.get_queue_items()]}\n"

        await response(ctx, msg)
