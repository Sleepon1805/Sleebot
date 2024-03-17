import logging
from typing import Optional, Dict, List

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy


class SpotifyHandler:
    def __init__(self):
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                cache_handler=spotipy.cache_handler.CacheFileHandler(cache_path='cache/spotify.cache')
            )
        )

    def get_artist_top_tracks(
            self, artist_name: str, limit=None, return_search: bool = True
    ) -> List[Dict] | List[str]:
        playlist_items = self._get_playlist_by_name(
            f"This is {artist_name}", sortby='popularity')

        limit = min(limit, len(playlist_items)) if limit else len(playlist_items)
        top_tracks = [item['track'] for item in playlist_items[:limit]]

        if return_search:
            top_tracks = self.tracks_to_yt_searches(top_tracks)
        return top_tracks

    def get_artist_mix(
            self, artist_name: str, limit=None, return_search: bool = True
    ) -> List[Dict] | List[str]:
        playlist_items = self._get_playlist_by_name(
            f"{artist_name} Mix")

        limit = min(limit, len(playlist_items)) if limit else len(playlist_items)
        tracks = [item['track'] for item in playlist_items[:limit]]

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

    def _get_playlist_by_name(self, playlist_name: str, sortby: str = None) -> Optional[List[Dict]]:
        searched_playlists = self.spotify.search(playlist_name, type='playlist')['playlists']['items']
        playlist = None
        for p in searched_playlists:
            if p['name'].lower() == playlist_name.lower():
                playlist = p

        if playlist is None:
            logging.warning(f"No playlist found for '{playlist_name}'")
            return []

        playlist_items = self.spotify.playlist_items(playlist['id'])['items']

        # TODO fix sorting
        if sortby and sortby in playlist_items[0]['track']:
            playlist_items = sorted(playlist_items, key=lambda x: x['track'][sortby], reverse=True)

        return playlist_items

    @staticmethod
    def tracks_to_yt_searches(tracks: List[Dict] | Dict) -> List[str]:
        if isinstance(tracks, dict):
            tracks = [tracks]
        searches = []
        for track in tracks:
            searches.append(
                f'{track["name"]} {track["artists"][0]["name"]}'
            )
        return searches


if __name__ == '__main__':
    from dotenv import load_dotenv
    from pprint import pprint
    load_dotenv()
    spotify_handler = SpotifyHandler()
    artist_to_search = 'Mass Hysteria'
    output = spotify_handler.get_artist_recommendations(artist_to_search)
    pprint(spotify_handler.tracks_to_yt_searches(output))
