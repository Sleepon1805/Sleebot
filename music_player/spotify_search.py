import os
import logging
from typing import Optional, Dict, List

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy


class SpotifyHandler:
    def __init__(self):
        os.makedirs('cache', exist_ok=True)
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                cache_handler=spotipy.cache_handler.CacheFileHandler(cache_path='cache/spotify.cache')
            )
        )

    def process_search(self, search: str, category=None) -> (Dict | None, str):
        if category:
            categories = [category]
        else:
            categories = ['playlist', 'album', 'artist', 'track']

        queried_items = []
        for category in categories:
            results = self.spotify.search(search, type=category, limit=5)
            queried_items = results[category + 's']['items']
            for item in queried_items:
                if item['name'].lower() == search.lower():
                    return item, f'Found {item['name']} in category {category}s.'
        out_msg = f'Could not find {search} in spotify.\n'
        if not category:
            out_msg += 'Try to specify search category by calling !play "<track|album|artist|playlist> {search}"'
        else:
            out_msg += f'Maybe you meant one of {[item['name'] for item in queried_items]}?'
        return None, out_msg

    def process_url(self, url: str) -> (Dict | None, str):
        if 'track' in url:
            item = self.spotify.track(url)
            out_msg = f'Found {item["name"]} in category tracks.'
        elif 'album' in url:
            item = self.spotify.album(url)
            out_msg = f'Found {item["name"]} in category albums.'
        elif 'artist' in url:
            item = self.spotify.artist(url)
            out_msg = f'Found {item["name"]} in category artists.'
        elif 'playlist' in url:
            item = self.spotify.playlist(url)
            out_msg = f'Found {item["name"]} in category playlists.'
        else:
            item = None,
            out_msg = f'Unknown spotify url: {url}'
        return item, out_msg

    def get_queries_from_spotify_object(
            self, item: Dict, category: str, ctx, get_recommendations=False, limit=None
    ) -> List[str]:
        if category == 'track':
            songs = [item]
        elif category == 'artist':
            songs = self.spotify.artist_top_tracks(item['id'])['tracks']
        elif category == 'album':
            songs = self.spotify.album(item['id'])['tracks']['items']
        elif category == 'playlist':
            playlist_items = self.spotify.playlist_items(item['id'], limit=limit)['items']
            songs = [item['track'] for item in playlist_items]
        else:
            logging.warning(f'Unknown category: {category}. Category must be one of: track, artist, album, playlist.')
            return []

        if get_recommendations:
            rec_limit = min(len(songs), 5)  # max 5 seed tracks
            recommendations = self.spotify.recommendations(
                seed_tracks=[songs['id'] for songs in songs[:rec_limit]],
                limit=limit
            )
            songs = recommendations['tracks']

        limit = min(limit, len(songs)) if limit else len(songs)
        songs = songs[:limit]

        queries = [
            f"{song['name']} - {song['artists'][0]['name']}"
            for song in songs
        ]
        return queries
