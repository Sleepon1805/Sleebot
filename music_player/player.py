"""
Source: https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
"""
import logging
import asyncio
from asyncio.timeouts import timeout
from discord.ext import commands
from random import shuffle

from music_player.source import YTDLSource
from music_player.embed import PlayerEmbed


class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    def __init__(self, ctx):
        self.bot: commands.Bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self._embed = PlayerEmbed()

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
            else:
                self._guild.voice_client.play(
                    source,
                    after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set)
                )

            await self.update_embed()
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.delete_cache()
            try:
                source.cleanup()  # FIXME
            except Exception as e:
                logging.warning(f'Failed to cleanup FFmpeg process: {e}')

            self.current = None

    async def add_to_queue(self, ctx, query: str):
        if "playlist?list=" in query:
            song_queries = await YTDLSource.extract_urls_from_playlist(query, self.bot.loop)
        else:
            song_queries = [query]

        for query in song_queries:
            try:
                audiosource = await YTDLSource.create_audiosource(
                    ctx, query, loop=self.bot.loop, download=self.download)
                await self.queue.put(audiosource)
                await self.update_embed()
            except Exception as e:
                logging.warning(e)  # FIXME logging format
                await ctx.send(f'```Could not add {query} to the queue.```', delete_after=20)

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))

    def get_queue_items(self):
        # FIXME
        return list(self.queue._queue)

    def shuffle_queue(self):
        # FIXME
        shuffle(self.queue._queue)

    async def update_embed(self):
        await self._embed.update(
            self.current,
            self.get_queue_items(),
            self._guild.voice_client.channel
        )

    async def send_new_embed_msg(self, ctx):
        await self.update_embed()
        await self._embed.resend_msg(ctx)

