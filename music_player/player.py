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

from music_player.youtube_handler import YTDLSource
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
                    source: YTDLSource = await self.queue.get()
            except asyncio.TimeoutError:
                await self.destroy()
                return

            self.current = source

            if self.vc is None:
                continue
            else:
                try:
                    await source.get_audiosource(self.bot.loop)
                    source.audiosource.volume = self.volume
                    self.vc.play(
                        source.audiosource,
                        after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set)
                    )
                except Exception as e:
                    logging.warning(e)
                    continue

            await self.update_embed()
            await self.next.wait()

            source.cleanup()

            self.current = None

    async def add_to_queue(self, ctx: commands.Context, query: str | List[str]):
        if isinstance(query, list):
            sources = [await YTDLSource.init_from_search(q, self.download, self.bot.loop, ctx) for q in query]
        elif "playlist?list=" in query:
            sources = await YTDLSource.init_from_playlist(query, self.download, self.bot.loop, ctx)
        else:
            sources = [await YTDLSource.init_from_url(query, self.download, self.bot.loop, ctx)]

        msg = await response(ctx, f'Processed 0/{len(sources)} songs')

        for i, s in enumerate(sources):
            msg = await edit(
                msg, content=msg.content.replace(f'{i}/{len(sources)}', f'{i+1}/{len(sources)}')
            )
            if not s.check():
                msg = await edit(
                    msg, content=msg.content + f'\n- Could not add {s.webpage_url}'
                )
            else:
                try:
                    await self.queue.put(s)
                    await self.update_embed()
                except Exception as e:
                    logging.warning(e)
                    msg = await edit(
                        msg, content=msg.content[:-3] + f'\n- Could not add {s.webpage_url}```'
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

        try:
            await self.vc.disconnect()
        except AttributeError:
            pass

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

