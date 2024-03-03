import discord
from discord.ext import commands
import yt_dlp
import asyncio

yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream))
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @staticmethod
    def playlist_to_urls(playlist_url, *, stream=False):
        data = ytdl.extract_info(playlist_url, download=not stream, process=False)
        for entry in data['entries']:
            filename = entry['url'] if stream else ytdl.prepare_filename(entry)
            yield filename


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """Join a voice channel"""
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()

    @commands.command()
    async def leave(self, ctx):
        """Leave current voice channel"""
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.command()
    async def play(self, ctx, *, url, stream=True):
        """Play audio from YouTube video URL"""

        await self.ensure_voice(ctx)

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=stream)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def playlist(self, ctx, *, url, stream=True):
        """Play audio from YouTube playlist URL"""

        await self.ensure_voice(ctx)

        lock = asyncio.Lock()
        urls = YTDLSource.playlist_to_urls(url, stream=stream)

        for url in urls:
            await lock.acquire()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=stream)
            await ctx.send(f'Now playing: {player.title}')
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else lock.release())

    @commands.command()
    async def stop(self, ctx):
        """Stop and leave voice channel"""

        await ctx.voice_client.disconnect()

    @commands.command()
    async def volume(self, ctx, volume: float):
        """Change the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        current_volume = ctx.voice_client.source.volume
        ctx.voice_client.source.volume = volume

        await ctx.send(f"Changed volume from {current_volume} to {volume}")

    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
