"""
Source: https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
"""
import os
import logging
import asyncio
from asyncio.timeouts import timeout
from functools import partial
from yt_dlp import YoutubeDL

import discord
from discord.ext import commands


ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'cache/%(extractor)s-%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, audio: discord.FFmpegPCMAudio, *, data, requester, source):
        super().__init__(audio)
        self.requester = requester

        self.source = source
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    def delete_cache(self):
        # TODO separate cached files for different guilds
        if isinstance(self.source, str) and os.path.isfile(self.source):
            # source.source is path to downloaded audio
            os.remove(self.source)

    @classmethod
    async def create_audiosource(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if download:
            source = ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author, source=source)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

    @classmethod
    async def extract_urls_from_playlist(cls, playlist_url, loop):
        assert "playlist?list=" in playlist_url
        to_run = partial(ytdl.extract_info, url=playlist_url, download=False, process=False)
        data = await loop.run_in_executor(None, to_run)
        urls = [entry['url'] for entry in data['entries']]
        return urls

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester, source=data)


class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume', 'download')

    def __init__(self, ctx):
        self.bot: commands.Bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None
        self.download = True

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            if self._guild.voice_client is None:
                continue

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(
                f'**Now Playing:** `{source.title}` requested by {source.requester}`')
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.delete_cache()
            try:
                source.cleanup()  # FIXME
            except Exception as e:
                logging.warning(f'Failed to cleanup FFmpeg process: {e}')

            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    async def add_to_queue(self, ctx, query: str):
        if "playlist?list=" in query:
            song_queries = await YTDLSource.extract_urls_from_playlist(query, self.bot.loop)
        else:
            song_queries = [query]

        for query in song_queries:
            try:
                audiosource = await YTDLSource.create_audiosource(
                    ctx, query, loop=self.bot.loop, download=self.download)
                await ctx.send(f'```Added {audiosource.title} to the queue.```', delete_after=20)
                await self.queue.put(audiosource)
            except Exception as e:
                logging.warning(e)  # FIXME logging format
                await ctx.send(f'```Could not add {query} to the queue.```', delete_after=20)

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))

    def get_queue_items(self):
        # FIXME
        return list(self.queue._queue)
