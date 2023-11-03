import datetime
import json
import random
import pyinputplus as pyip
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import Credentials

def authenticate_spotify():
    scope = "playlist-read-private user-top-read user-library-read playlist-modify-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=Credentials.client_id,
                                                   client_secret=Credentials.client_secret,
                                                   redirect_uri=Credentials.redirect_uri,
                                                   scope=scope,
                                                   cache_path="token_cache"))
    return sp

def get_user_input():
    input_source = pyip.inputChoice(['A', 'B'], prompt="Choose source to build music taste profile (A: Historic data, B: Specific playlist): ", caseSensitive=False)
    archive_activation = pyip.inputYesNo(prompt="Exclude songs from previous executions (yes or no)?: ", caseSensitive=False)
    playlist_name = input("Enter the new playlist name: ")
    return input_source, archive_activation, playlist_name

def get_playlist_id(sp, username, playlist_name):
    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            return playlist['id']
    return None

def get_recommendations(sp, seed_tracks, limit, market):
    uris_list = []
    release_date_min = datetime.datetime.now() - datetime.timedelta(days=15 * 365)
    for seed in seed_tracks:
        recommendations = sp.recommendations(seed_tracks=[seed], limit=limit, market=market)
        for track in recommendations['tracks']:
            release_date = track['album']['release_date']
            r_date_dt = datetime.datetime.strptime(release_date.split('-')[0], "%Y")
            if r_date_dt >= release_date_min:
                uris_list.append(track['uri'])
    return uris_list

def create_playlist(sp, user_id, playlist_name, tracks):
    playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
    sp.playlist_add_items(playlist['id'], tracks)
    return playlist['external_urls']['spotify']

def main():
    sp = authenticate_spotify()
    user_id = Credentials.user_id
    market = "US"

    input_source, archive_activation, playlist_name = get_user_input()

    if input_source.upper() == 'B':
        playlist_id = get_playlist_id(sp, user_id, playlist_name)
        tracks = sp.playlist_items(playlist_id)
        seed_tracks = [track['track']['id'] for track in tracks['items']]
    else:
        top_tracks = sp.current_user_top_tracks(limit=20, time_range='medium_term')
        seed_tracks = [track['id'] for track in top_tracks['items']]

    uris_list = get_recommendations(sp, seed_tracks, limit=5, market=market)
    new_tracks = set(uris_list) - set([item['track']['uri'] for item in sp.current_user_saved_tracks()['items']])

    if archive_activation.lower() == 'yes':
        with open(Credentials.archive_file_path + "Old_Recommended_Tracks.txt", "r") as file:
            archived_tracks = set(file.read().split('| '))
        new_tracks -= archived_tracks

    playlist_url = create_playlist(sp, user_id, playlist_name, list(new_tracks))
    print(f'Your new playlist is ready at {playlist_url}')

    if archive_activation.lower() == 'yes':
        with open(Credentials.archive_file_path + "Old_Recommended_Tracks.txt", "a") as file:
            file.write(' | '.join(list(new_tracks)) + '|')

if __name__ == "__main__":
    main()
