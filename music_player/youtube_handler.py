import os
import asyncio
import logging
from functools import partial
from typing import Dict, List
import discord
from yt_dlp import YoutubeDL
from pytube import Playlist, Search


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
    'source_address': '0.0.0.0',  # ipv6 addresses cause issues sometimes
    'noprogress': True,
}

ytdl = YoutubeDL(ytdlopts)


class Track:
    def __init__(self, data: Dict[str, str], requester: discord.abc.User):
        self.data = data
        self.requester = requester
        self.filename: str | None = None
        self.audiosource: discord.PCMVolumeTransformer | Dict | None = None

    @property
    def title(self):
        return self.data['title']

    @property
    def artist(self):
        if 'artist' in self.data:
            return self.data['artist']
        else:
            return None

    @property
    def yt_url(self):
        if 'webpage_url' in self.data:
            return self.data['webpage_url']
        elif 'original_url' in self.data:
            return self.data['original_url']
        elif 'url' in self.data:
            return self.data['url']
        else:
            return None

    @property
    def duration(self):
        return self.data['duration'] if 'duration' in self.data else None

    @property
    def thumbnail(self):
        if 'thumbnail' in self.data:
            return self.data['thumbnail']
        elif 'thumbnails' in self.data:
            return self.data['thumbnails'][0]['url']
        else:
            return None

    @staticmethod
    async def get_urls(query: str) -> List[str]:
        # TODO: parallelize this
        if "youtube.com" in query or "youtu.be" in query:
            if "list=" in query:
                urls = list(Playlist(query).video_urls)
            else:
                urls = [query]
        else:
            urls = [Search(query).results[0].watch_url]
        return urls

    @classmethod
    async def from_url(cls, url: str, loop: asyncio.AbstractEventLoop, ctx):
        to_run = partial(ytdl.extract_info, url=url, download=False, process=True)
        data = await loop.run_in_executor(None, to_run)
        requester = ctx.author
        return cls(data, requester)

    async def get_audiosource(self, loop: asyncio.AbstractEventLoop, download: bool = True):
        if download:
            loop = loop or asyncio.get_event_loop()
            to_run = partial(ytdl.download, url_list=self.yt_url)
            await loop.run_in_executor(None, to_run)
            self.filename = ytdl.prepare_filename(self.data)
            audiosource = discord.FFmpegPCMAudio(self.filename, before_options='-nostdin', options='-vn')
            self.audiosource = discord.PCMVolumeTransformer(audiosource)  # AudioSource with volume control
        else:
            self.audiosource = self.data
        return self.audiosource

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
