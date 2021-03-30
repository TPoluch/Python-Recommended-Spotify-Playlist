# Generate Customized Recommended Playlist

This python script generates a playlist tailored to the users music tastes.

# How it works:

1. Reads in the top n songs listened to by the user over 3 time spans - short-term, medium-term, long-term (assigns a rank 1-n based on most-least listened too for each time span)

      Pulls the audio features (energy, danceability, loudness, etc) for each track
      
      Assigns a weight to each track, weights are based on 2 factors:
    * Tracks are given a weight for their timespan (long-term being weighted highest and short-term lowest) 
    * They are also weighted based on the rank they have within their respective time-span

      
    Calculates the target value for each audio feature using the weighted averages of the tracks
    
2. Pulls in all songs currently in the users library

3. Gets recommended songs based on the genres entered by the user and the target audio feature values established earlier
User can choose the minimum release year they want the recommended tracks to have 

4. Compares list of recommended songs to the songs currently in the users library and excludes any that the user already has

5. Creates/populates playlist

```python

import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import requests
import json
import numpy as np
import datetime
import random

# User specific/preference variables
# MUST ADD SPOTIPY ENV VARIABLES
# SPOTIPY_CLIENT_ID: 'your_client_id'
# SPOTIPY_CLIENT_SECRET: 'your_client_secret'
# SPOTIPY_REDIRECT_URI: 'your_redirect_url'

client_id = 'your_client_id'
client_secret = 'your_client_secret'
redirect_uri = 'your_redirect_url'
user_id = "your_user_id"
sample_size = 15 # number of songs from each time span (short,medium,long) to use as base for creating target audio features
pull_songs_released_in_last_n_years = 5 # only add songs from n years ago and after
playlist_name = 'Python Recommended'
genres = ["hip-hop", "happy", "party", "pop", "chill"]  #link to possible genres -- https://developer.spotify.com/console/get-available-genre-seeds/
limit = 100  #number of songs from each genre

# Get First Token

AUTH_URL = 'https://accounts.spotify.com/api/token'

auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
})

auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']
token = access_token

# Read top 50 tracks from short,medium, and long time spans and find the weighted average audio attr values
# Weighting from highest to lowest is long-short time span and then the rank of the individual within each of those time spans respectively

auth_manager = SpotifyClientCredentials(client_id=client_id,
                                        client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               scope='user-library-read', redirect_uri=redirect_uri))

ranges = ['short_term', 'medium_term', 'long_term']
for sp_range in ranges:
    results = sp.current_user_top_tracks(time_range=sp_range, limit=sample_size)
    for i, item in enumerate(results['items']):
        if sp_range == 'short_term':
            range = 1
        elif sp_range == 'medium_term':
            range = 2
        else:
            range = 3
        time_range = range + (sample_size - i) / 100
        track_info = sp.track(item['id'])
        rank = int(i)
        track_features = sp.audio_features(item['id'])

        track_id = track_info['id']
        name = track_info['name']
        album = track_info['album']['name']
        artist = track_info['album']['artists'][0]['name']
        release_date = track_info['album']['release_date']
        popularity = track_info['popularity']

        acousticness = track_features[0]['acousticness']
        danceability = track_features[0]['danceability']
        energy = track_features[0]['energy']
        loudness = track_features[0]['loudness']
        speechiness = track_features[0]['speechiness']
        instrumentalness = track_features[0]['instrumentalness']
        liveness = track_features[0]['liveness']
        tempo = track_features[0]['tempo']
        valence = track_features[0]['valence']

        track = [rank, track_id, time_range, acousticness, danceability, energy, loudness, speechiness,
                 instrumentalness, liveness, tempo, valence]

        df = pd.DataFrame(track).T.values.tolist()
        df_final = pd.DataFrame(df, columns=['rank', 'track_id', 'time_range', 'acousticness', 'danceability',
                                             'energy', 'loudness', 'speechiness', 'instrumentalness',
                                             'liveness', 'tempo', 'valence'])

target_acousticness = round(np.average(df_final['acousticness'], weights=df_final['time_range']), 4)
target_danceability = round(np.average(df_final['danceability'], weights=df_final['time_range']), 4)
target_energy = round(np.average(df_final['energy'], weights=df_final['time_range']), 4)
target_loudness = round(np.average(df_final['loudness'], weights=df_final['time_range']), 4)
target_speechiness = round(np.average(df_final['speechiness'], weights=df_final['time_range']), 4)
target_instrumentalness = round(np.average(df_final['instrumentalness'], weights=df_final['time_range']), 4)
target_liveness = round(np.average(df_final['liveness'], weights=df_final['time_range']), 4)
target_tempo = round(np.average(df_final['tempo'], weights=df_final['time_range']), 4)
target_valence = round(np.average(df_final['valence'], weights=df_final['time_range']), 4)

# Get current songs library to compare with recommended set

library_scope = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                          client_secret=client_secret,
                                                          scope='user-library-read',
                                                          redirect_uri=redirect_uri))
tracks_list = []

def show_tracks(results):
    for item1 in results['items']:
        track_uri = item1['track']
        tracks_list.append(track_uri['uri'])


results = library_scope.current_user_saved_tracks()
show_tracks(results)

while results['next']:
    results = library_scope.next(results)
    show_tracks(results)

tracks_set = set(tracks_list)

# Get recommended set

recommendations_url = "https://api.spotify.com/v1/recommendations?"
market = "US"
uris_list = []

release_date_min = datetime.datetime.now() - datetime.timedelta(days=pull_songs_released_in_last_n_years*365)

for genre in genres:
    query = f'{recommendations_url}limit={limit}&market={market}&seed_genres={genre}&target_acousticness={target_acousticness}' \
            f'&target_danceability={target_danceability}&target_energy={target_energy}&target_loudness={target_loudness}' \
            f'&target_speechiness={target_speechiness}&target_instrumentalness={target_instrumentalness}&target_liveness={target_liveness}' \
            f'&target_tempo={target_tempo}&target_valence={target_valence}'
    response = requests.get(query,
                            headers={"Content-Type": "application/json",
                                     "Authorization": f"Bearer {token}"})
    json_response = response.json()
    for i, j in enumerate(json_response['tracks']):
        r_date_str = (j['album']['release_date'])
        uri_original = (j['uri'])

        # filtering any songs out that are older than the min release date wanted

        if len(r_date_str) == 4:
            r_date_str = r_date_str[:4]
            r_date_dt = datetime.datetime.strptime(r_date_str, "%Y")
        elif len(r_date_str) == 7:
            r_date_str = r_date_str[:7]
            r_date_dt = datetime.datetime.strptime(r_date_str, "%Y-%m")
        else:
            r_date_dt = datetime.datetime.strptime(r_date_str, "%Y-%m-%d")

        if r_date_dt >= release_date_min:
            uris_list.append(uri_original)
            print(genre+" - "+f"{i + 1}) \"{j['name']}\" by {j['artists'][0]['name']}")

# Make sure recommended songs are not already in users library


uris_to_set = set(uris_list)
uri = list(uris_to_set.difference(tracks_set))

# Max playlist length is 75

if len(uri)>75:
    random.shuffle(uri)
    uri = uri[:75]
else:
    random.shuffle(uri)
print(uri)

# Create Playlist (need new token for write access)

webpage_for_token = f"https://developer.spotify.com/console/post-playlists/"
print("Go here and grab token: " + webpage_for_token)
token_input = input("Enter token: ")
print("Enter token: " + token_input)
print(token_input)
token2 = token_input

playlist_endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"

request_body = json.dumps({
    "name": playlist_name,
    "description": str(datetime.datetime.now()),
    "public": False
})
response = requests.post(url=playlist_endpoint, data=request_body, headers={"Content-Type": "application/json",
                                                                        "Authorization": f"Bearer {token2}"})

url = response.json()['external_urls']['spotify']

# Add songs to playlist

playlist_id = response.json()['id']

tracks_to_list_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

request_body = json.dumps({
    "uris": uri
})
response = requests.post(url=tracks_to_list_url, data=request_body, headers={"Content-Type": "application/json",
                                                                        "Authorization": f"Bearer {token2}"})

print(f'Your playlist is ready at {url}')

```
