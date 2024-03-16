import os
import asyncio
from functools import partial
from datetime import timedelta

import discord
from yt_dlp import YoutubeDL


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

    def __repr__(self):
        if 'artist' in self.data and 'track' in self.data:
            song_str = f'`{self.data['track']}` by `{self.data['artist']}`'
        else:
            song_str = f'`{self.title}`'

        requester_str = f'requested by `{self.requester.display_name}`'

        duration_str = f'({timedelta(seconds=self.data['duration'])})'
        duration_str = duration_str[2:] if duration_str.startswith('0:') else duration_str

        return ' '.join([song_str, requester_str, duration_str])

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
