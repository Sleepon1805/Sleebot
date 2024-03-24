from datetime import timedelta
from typing import Optional, List
import discord

from music_player.youtube_handler import YTDLSource


class PlayerEmbed:
    def __init__(self):
        self.embed: discord.Embed | None = None  # discord.Embed about current player status
        self.msg: discord.Message | None = None  # object of message with self.embed

    async def update(
            self,
            current: Optional[YTDLSource] = None,
            queue: List[YTDLSource] = None,
            channel: discord.VoiceChannel = None
    ):
        # Now playing
        if current:
            current_str = self.source_to_str(current)
            channel_playing = ' in ' + channel.name if channel else ''
            embed = discord.Embed(
                title=f'Now Playing' + channel_playing,
                description=f'{current_str}\n [{current.web_url}]',
                color=discord.Color.blue()
            )
            if 'thumbnail' in current.data:
                embed.set_thumbnail(url=current.data['thumbnail'])
        else:
            embed = discord.Embed(
                title=f'Not playing anything right now',
                description='You can add songs to the queue with !play',
                color=discord.Color.blue()
            )

        # Queue
        if len(queue) > 0:
            songs_queue = queue if len(queue) <= 5 else queue[:5]
            field_value = '\n'.join(f'{num}. {self.source_to_str(source)}' for num, source in enumerate(songs_queue))
            if len(queue) > 5:
                field_value += f'\nAnd {len(queue) - 5} more...'
            embed.add_field(
                name=f'Queued songs: {len(queue)}',
                value=field_value,
                inline=False
            )

            # footer: remaining time
            queue_time = sum([source.data['duration'] for source in queue])
            embed.set_footer(text="Estimated queue time: " + str(timedelta(seconds=queue_time)))

        # update self
        self.embed = embed

        # edit existing message
        if self.msg:
            try:
                await self.msg.edit(embed=self.embed)
            except discord.HTTPException:
                self.msg = None

    async def resend_msg(self, ctx, reply: bool = False):
        """ Resend self.embed as a new message in text channel. """
        if self.msg:
            await self.msg.delete()
        if reply:
            self.msg = await ctx.reply(embed=self.embed)
        else:
            self.msg = await ctx.channel.send(embed=self.embed)

    @staticmethod
    def source_to_str(source: YTDLSource):
        if 'artist' in source.data and 'track' in source.data:
            song_str = f'`{source.data['track']}` by `{source.data['artist']}`'
        else:
            song_str = f'`{source.title}`'

        requester_str = f'requested by `{source.requester.display_name}`'

        duration_str = f'({timedelta(seconds=source.data['duration'])})'

        return ' '.join([song_str, requester_str, duration_str])
