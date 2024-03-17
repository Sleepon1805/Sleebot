import os
import asyncio
from functools import partial

import discord
from yt_dlp import YoutubeDL


ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'cache/ytdl/%(extractor)s-%(id)s.%(ext)s',
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


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, audio: discord.FFmpegPCMAudio, *, data, requester, source):
        super().__init__(audio)
        self.requester = requester

        self.source = source
        self.data = data
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
    async def create_audiosource(cls, ctx, url: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=url, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # playlist should be handled in player.py
            data = data['entries'][0]

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
