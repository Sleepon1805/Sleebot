from datetime import timedelta
from typing import Optional, List
import discord

from music_player.track import Track
from utils import send, edit


class PlayerEmbed:
    def __init__(self):
        self.embed: discord.Embed | None = None  # discord.Embed about current player status
        self.msg: discord.Message | None = None  # object of message with self.embed

    async def update(
            self,
            current: Optional[Track] = None,
            queue: List[Track] = None,
            channel: discord.VoiceChannel = None
    ):
        # Now playing
        if current:
            current_str = self.track_to_str(current)
            channel_playing = ' in ' + channel.name if channel else ''
            embed = discord.Embed(
                title=f'Now Playing' + channel_playing,
                description=f'{current_str}\n [{current.url}]',
                color=discord.Color.blue()
            )
            if current.thumbnail is not None:
                embed.set_thumbnail(url=current.thumbnail)
        else:
            embed = discord.Embed(
                title=f'Not playing anything right now',
                description='Type !help or /help to see available commands.',
                color=discord.Color.blue()
            )

        # Queue
        if len(queue) > 0:
            songs_queue = queue if len(queue) <= 5 else queue[:5]
            field_value = '\n'.join(f'{num}. {self.track_to_str(track)}' for num, track in enumerate(songs_queue))
            if len(queue) > 5:
                field_value += f'\nAnd {len(queue) - 5} more...'
            embed.add_field(
                name=f'Queued songs: {len(queue)}',
                value=field_value,
                inline=False
            )

            # footer: remaining time
            queue_time = sum([source.duration for source in queue if source.duration])
            footer_text = "Estimated queue time: " + str(timedelta(seconds=queue_time))
            unknown_duration = len([source for source in queue if not source.duration])
            if unknown_duration > 0:
                footer_text += " + " + str(unknown_duration) + " x unknown"
            embed.set_footer(text=footer_text)

        # update self
        self.embed = embed

        # edit existing message
        if self.msg:
            await edit(self.msg, embed=self.embed)

    async def resend_msg(self, ctx):
        """ Resend self.embed as a new message in text channel. """
        if self.msg:
            await self.msg.delete()
        self.msg = await send(ctx, embed=self.embed)

    @staticmethod
    def track_to_str(track: Track):
        if track.artist is not None:
            song_str = f'`{track.title}` by `{track.artist}`'
        else:
            song_str = f'`{track.title}`'

        requester_str = f'requested by `{track.requester.display_name}`'

        duration_str = f'({timedelta(seconds=track.duration)})' if track.duration else '(unknown)'

        return ' '.join([song_str, requester_str, duration_str])
