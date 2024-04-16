import os
import asyncio
import logging
from functools import partial
from typing import Dict
import discord
from yt_dlp import YoutubeDL
from dataclasses import dataclass


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


@dataclass
class Track:
    title: str
    duration: int
    requester: discord.abc.User
    artist: str | None = None
    url: str | None = None
    thumbnail: str | None = None

    @classmethod
    async def from_url(cls, url: str, requester: discord.abc.User, loop: asyncio.AbstractEventLoop):
        to_run = partial(ytdl.extract_info, url=url, download=False, process=False)
        data = await loop.run_in_executor(None, to_run)
        track = cls(
            title=data['title'],
            duration=data['duration'],
            requester=requester,
            artist=data['artist'] if 'artist' in data else None,
            url=data['webpage_url'],
            thumbnail=data['thumbnails'][0]['url'] if 'thumbnails' in data else None,
        )
        return track

    @classmethod
    async def from_playlist(cls, playlist_url: str, requester: discord.abc.User, loop: asyncio.AbstractEventLoop):
        assert "playlist?list=" in playlist_url
        to_run = partial(ytdl.extract_info, url=playlist_url, download=False, process=False)
        data = await loop.run_in_executor(None, to_run)
        tracks = []
        for entry in data['entries']:
            track = cls(
                title=entry['title'],
                duration=entry['duration'],
                requester=requester,
                artist=entry['artist'] if 'artist' in entry else None,
                url=entry['url'],
                thumbnail=entry['thumbnails'][0]['url'] if 'thumbnails' in entry else None,
            )
            tracks.append(track)
        return tracks

    @classmethod
    async def from_search(cls, query: str, requester: discord.abc.User, loop: asyncio.AbstractEventLoop):
        query = query.replace(':', '')
        to_run = partial(ytdl.extract_info, url=query, download=False, process=False)
        data = await loop.run_in_executor(None, to_run)
        data = data['entries'][0]  # text search gives playlist with one entry out
        track = cls(
            title=data['title'],
            duration=data['duration'],
            requester=requester,
            artist=data['artist'] if 'artist' in data else None,
            url=None,
        )
        return track

    async def process(self, download: bool, loop: asyncio.AbstractEventLoop):
        # process track
        if self.url is None:
            self.url = f'{self.title} by {self.artist}' if self.artist else self.title
        to_run = partial(ytdl.extract_info, url=self.url, download=download, process=True)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            data = data['entries'][0]

        # update track info
        if 'title' in data:
            self.title = data['title']
        if 'duration' in data:
            self.duration = data['duration']
        if 'artist' in data:
            self.artist = data['artist']
        if 'webpage_url' in data:
            self.url = data['webpage_url']
        if 'thumbnails' in data:
            self.thumbnail = data['thumbnails'][0]['url']

        return data


class YTDLSource(Track):
    def __init__(self, track: Track, download=True):
        super().__init__(track.title, track.duration, track.requester, track.artist, track.url)

        # YTDL properties
        self.download = download
        self.ffmpegopts = {
            'before_options': '-nostdin',
            'options': '-vn'
        }
        self.filename: str | None = None
        self.audiosource: discord.PCMVolumeTransformer | Dict | None = None

        self._check_availability()

    def _check_availability(self):
        # check track availability
        if self.title == "[Private video]":
            raise ValueError(f'Could not add private video {self.url}')
        elif self.title == "[Deleted video]":
            raise ValueError(f'Could not add deleted video {self.url}')

    async def get_yt_audiosource(self, loop: asyncio.AbstractEventLoop):
        loop = loop or asyncio.get_event_loop()

        data = await self.process(self.download, loop)

        if self.download:
            self.filename = ytdl.prepare_filename(data)
            audiosource = discord.FFmpegPCMAudio(self.filename, **self.ffmpegopts)
            self.audiosource = discord.PCMVolumeTransformer(audiosource)  # AudioSource with volume control
        else:
            self.audiosource = data

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
