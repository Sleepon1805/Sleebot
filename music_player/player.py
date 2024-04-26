"""
Source: https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34
"""
import logging
import asyncio
from asyncio.timeouts import timeout
import discord
from discord.ext import commands
from random import shuffle
from typing import List

from music_player.youtube_handler import Track
from music_player.embed import PlayerEmbed
from utils import response, edit


class MusicPlayer:
    """
    A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    def __init__(self, bot: commands.Bot, voice_client: discord.VoiceClient | None):
        self.bot: commands.Bot = bot
        self.vc = voice_client
        self.embed = PlayerEmbed()

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.volume = .5
        self.current = None
        self.download = True

        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(60):
                    track: Track = await self.queue.get()
            except asyncio.TimeoutError:
                await self.destroy()
                return

            self.current = track

            if self.vc is None:
                continue
            else:
                try:
                    await track.get_audiosource(self.bot.loop)
                    track.audiosource.volume = self.volume
                    self.vc.play(
                        track.audiosource,
                        after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set)
                    )
                except Exception as e:
                    logging.warning(e)
                    continue

            await self.update_embed()
            await self.next.wait()

            track.cleanup()
            self.current = None

    async def add_to_queue(self, ctx: commands.Context, queries: List[str]):
        msg = await response(ctx, 'Processing your query...')

        urls = []
        for query in queries:
            urls.extend(await Track.get_urls(query))
        msg = await edit(msg, content=f'Processed 0/{len(urls)} tracks')

        for i, url in enumerate(urls):
            try:
                track = await Track.from_url(url, loop=self.bot.loop, ctx=ctx)
                await self.queue.put(track)
                await self.update_embed()
            except Exception as e:
                logging.warning(e)
                msg = await edit(
                    msg, content=msg.content + f'\n- Could not add {url}'
                )
            msg = await edit(
                msg, content=msg.content.replace(f'{i}/{len(urls)}', f'{i+1}/{len(urls)}')
            )

    async def destroy(self):
        """Disconnect and cleanup the player."""
        await self.update_embed()

        # delete all downloaded audiofiles
        queue = self.get_queue_items()
        for source in queue:
            source.cleanup()
        # clear queue
        self.queue = asyncio.Queue()
        await self.update_embed()

        try:
            await self.vc.disconnect()
        except AttributeError:
            pass

        if self.vc.guild.id in self.bot.cogs['Music'].players:
            del self.bot.cogs['Music'].players[self.vc.guild.id]

    def get_queue_items(self):
        # FIXME
        return list(self.queue._queue)

    def shuffle_queue(self):
        # FIXME
        shuffle(self.queue._queue)

    async def update_embed(self):
        await self.embed.update(
            self.current,
            self.get_queue_items(),
            self.vc.channel
        )

    async def send_new_embed_msg(self, ctx: commands.Context):
        await self.update_embed()
        await self.embed.resend_msg(ctx)

