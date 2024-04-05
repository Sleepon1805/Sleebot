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

    def get_tracks_from_spotify_object(
            self, item: Dict, category: str, limit=None, return_search: bool = True
    ) -> List[Dict] | List[str]:
        if category == 'track':
            tracks = [item]
        elif category == 'artist':
            tracks = self.spotify.artist_top_tracks(item['id'])['tracks']
        elif category == 'album':
            tracks = self.spotify.album(item['id'])['tracks']['items']
        elif category == 'playlist':
            playlist_items = self.spotify.playlist_items(item['id'], limit=limit)['items']
            tracks = [item['track'] for item in playlist_items]
        else:
            logging.warning(f'Unknown category: {category}. Category must be one of: track, artist, album, playlist.')
            return []

        limit = min(limit, len(tracks)) if limit else len(tracks)
        tracks = tracks[:limit]

        if return_search:
            tracks = self.tracks_to_yt_searches(tracks)
        return tracks

    def get_artist_recommendations(
            self, artist_name: str, limit=None, return_search: bool = True
    ) -> List[Dict] | List[str]:
        artist = self._get_artist_by_name(artist_name)

        if artist is None:
            logging.warning(f'No artist found for {artist_name}')
            return []

        recommendations = self.spotify.recommendations(seed_artists=[artist['id']], limit=limit)['tracks']

        if return_search:
            recommendations = self.tracks_to_yt_searches(recommendations)
        return recommendations

    def _get_artist_by_name(self, artist_name: str) -> Optional[Dict]:
        searched_artists = self.spotify.search(artist_name, type='artist')['artists']['items']
        searched_artists = sorted(searched_artists, key=lambda x: x['followers']['total'], reverse=True)

        artist = None
        for a in searched_artists:
            if a['name'].lower() == artist_name.lower():
                artist = a
        return artist

    @staticmethod
    def tracks_to_yt_searches(tracks: List[Dict] | Dict) -> List[str]:
        if isinstance(tracks, dict):
            tracks = [tracks]
        searches = []
        for track in tracks:
            searches.append(
                f'{track["name"]} - {track["artists"][0]["name"]}'
            )
        return searches
