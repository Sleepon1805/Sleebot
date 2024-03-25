import os
import asyncio
import logging
from functools import partial
from typing import Dict
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

ytdl = YoutubeDL(ytdlopts)


class YTDLSource:

    def __init__(self, data: Dict[str, str], download: bool):
        self.data = data
        self.download = download

        self.ffmpegopts = {
            'before_options': '-nostdin',
            'options': '-vn'
        }

        self.filename: str | None = None
        self.audiosource: discord.PCMVolumeTransformer | Dict | None = None

    @property
    def title(self):
        return self.data['title'] if 'title' in self.data else None

    @property
    def webpage_url(self):
        if 'webpage_url' in self.data:
            return self.data['webpage_url']
        elif 'url' in self.data:
            return self.data['url']
        else:
            return None

    @property
    def requester(self):
        return self.data['requester'] if 'requester' in self.data else None

    @property
    def duration(self):
        return self.data['duration'] if 'duration' in self.data else 120

    async def get_audiosource(self, loop: asyncio.AbstractEventLoop):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=self.webpage_url, download=self.download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # playlist should be handled in other place
            data = data['entries'][0]

        if self.download:
            self.filename = ytdl.prepare_filename(data)
            audiosource = discord.FFmpegPCMAudio(self.filename, **self.ffmpegopts)
            self.audiosource = discord.PCMVolumeTransformer(audiosource)  # AudioSource with volume control
        else:
            self.audiosource = self.data

    @classmethod
    async def init_from_playlist(cls, playlist_url: str, download: bool, loop: asyncio.AbstractEventLoop, ctx):
        assert "playlist?list=" in playlist_url
        to_run = partial(ytdl.extract_info, url=playlist_url, download=False, process=False)
        data = await loop.run_in_executor(None, to_run)
        sources = []
        for entry in data['entries']:
            entry['requester'] = ctx.author
            sources.append(cls(entry, download))
        return sources

    @classmethod
    async def init_from_url(cls, url: str, download: bool, loop: asyncio.AbstractEventLoop, ctx):
        # URL can be either a search query or a direct link
        to_run = partial(ytdl.extract_info, url=url, download=False, process=False)
        data = await loop.run_in_executor(None, to_run)
        data['requester'] = ctx.author
        return cls(data, download)

    def cleanup(self):
        # Delete downloaded audio file
        if isinstance(self.filename, str) and os.path.isfile(self.filename):
            # source.source is path to downloaded audio
            os.remove(self.filename)

        # Make sure the FFmpeg process is cleaned up.
        if self.audiosource:
            try:
                self.audiosource.cleanup()  # FIXME
            except Exception as e:
                logging.warning(f'Failed to cleanup FFmpeg process: {e}')

    def check(self) -> bool:
        if self.title == '[Private video]':
            logging.warning(f'Private video: {self.webpage_url}')
            return False
        return True
