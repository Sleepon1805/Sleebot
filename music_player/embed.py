from datetime import timedelta
from typing import Optional, List
import discord

from music_player.source import YTDLSource


class PlayerEmbed:
    def __init__(self):
        self.embed = None  # discord.Embed about current player status
        self.msg = None  # object of message with self.embed

    async def update(
            self,
            current: Optional[YTDLSource] = None,
            queue: List[YTDLSource] = None,
            channel: discord.VoiceChannel = None
    ):
        # Now playing
        if current:
            channel_playing = ' in ' + channel.name if channel else ''
            embed = discord.Embed(
                title=f'Now Playing' + channel_playing,
                description=f'{current}\n [{current.web_url}]',
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
            field_value = '\n'.join(f'{num}. {source}' for num, source in enumerate(queue))
            if len(field_value) > 1024:
                field_value = '\n'.join(f'{num}. {source}' for num, source in enumerate(queue[:10]))
                field_value += f'\n and {len(queue) - 10} more...'
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
            await self.msg.edit(embed=self.embed)

    async def resend_msg(self, ctx):
        if self.msg:
            await self.msg.delete()
        self.msg = await ctx.send(embed=self.embed)
