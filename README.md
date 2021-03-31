# Generates a User-Unique Spotify Playlist

This python script generates a playlist tailored to the users music tastes through use of Spotify's API. It dechipers the users music preferences through analysis of their favorite songs, audio feature tendencies, and other key factors.

# How it works:

1. Reads in the top 'n' tracks and their related details for tracks listened to by the user over 3 time spans - short-term, medium-term, long-term (assigns a rank 1,2,3...n based on most-least listened to for each time span)

2. Each track pulled in step 1 gets 'n' recommended tracks by using the track as a "seed track" and using its audio features (energy, danceability, loudness, etc) values as the target aduio feature values for the possible recommended songs
      
3. Pulls in all tracks currently in the users library and compares it to the list of recommended tracks. Any recommended tracks that are already in the user's library are removed from the recommended list.

4. Creates Playlist

5. Populates playlist

```python

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import requests
import json
import datetime
import random

# MUST ADD SPOTIPY ENV VARIABLES
# SPOTIPY_CLIENT_ID: 'your_client_id'
# SPOTIPY_CLIENT_SECRET: 'your_client_secret'
# SPOTIPY_REDIRECT_URI: 'your_redirect_url'

# USER VARIABLES
client_id = 'your_client_id'
client_secret = 'your_client_secret'
redirect_uri = 'your_redirect_url'
user_id = 'your_user_id'

# PREFERENCE VARIABLES
sample_size = 10  # number of songs from each time span (short,medium,long)
n_years = 5  # only add songs released within the  last n years
limit = 5  # number of recommended songs to pull for each seed track
playlist_name = 'Python Recommended'
max_playlist_len = 75

# GET TOKEN FOR API CALLS THAT DON'T REQUIRE USER AUTHORIZATION
AUTH_URL = 'https://accounts.spotify.com/api/token'

auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
})

auth_response_data = auth_response.json()
access_token = auth_response_data['access_token']
token = access_token

auth_manager = SpotifyClientCredentials(client_id=client_id,
                                        client_secret=client_secret)

# STEP 1 - PULL TOP [sample_size] TRACKS FOR EACH TIME SPAN

# VARIABLES
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               scope='user-library-read', redirect_uri=redirect_uri))
recommendations_url = "https://api.spotify.com/v1/recommendations?"
market = "US"
uris_list = []
list_one = []
release_date_min = datetime.datetime.now() - datetime.timedelta(days=n_years * 365)
ranges = ['short_term', 'medium_term', 'long_term']

# LOOP THROUGH EACH TIME SPAN PULLING [sample_size] AMOUNT OF TRACKS AND THEIR DETAILS TO CREATE A LIST
for sp_range in ranges:
    results = sp.current_user_top_tracks(time_range=sp_range, limit=sample_size)
    for i, item in enumerate(results['items']):

        # CREATE NEW RANK FOR TRACKS TO TAKE INTO ACCOUNT THEIR TIME SPAN
        if sp_range == 'short_term':
            range = 1
        elif sp_range == 'medium_term':
            range = 2
        else:
            range = 3
        time_range = range + (sample_size - i) / 100
        track_info = sp.track(item['id'])
        rank = int(range) * 10 + ((limit - 1) - int(i))
        track_features = sp.audio_features(item['id'])
        seed = track_info['id']
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
        list_one.append([rank, seed, time_range, acousticness, danceability, energy, loudness, speechiness,
                         instrumentalness, liveness, tempo, valence])
        list_one.sort(reverse=True)

        # STEP 2 - PULL IN [limit] AMOUNT OF RECOMMENDED TRACKS FOR EACH TRACK FROM ABOVE

        # USE TRACK FROM ABOVE AS THE SEED AND ITS AUDIO FEATURES AS TARGET AUDIO FEATURES
        query = f'{recommendations_url}limit={limit}&market={market}&seed_tracks={seed}&target_acousticness={acousticness}' \
                f'&target_danceability={danceability}&target_energy={energy}&target_loudness={loudness}' \
                f'&target_speechiness={speechiness}&target_instrumentalness={instrumentalness}&target_liveness={liveness}' \
                f'&target_tempo={tempo}&target_valence={valence}'
        response = requests.get(query,
                                headers={"Content-Type": "application/json",
                                         "Authorization": f"Bearer {token}"})
        json_response = response.json()

        # PULL RECOMMENDED TRACKS URIS'
        for y, j in enumerate(json_response['tracks']):
            r_date_str = (j['album']['release_date'])
            uri_original = (j['uri'])

            # CLEAN RELEASE_DATE FIELD AND CHANGE ITS TYPE TO DATETIME; FILTER OUT ANY TRACKS > n_years OLD
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
                print(f"{y + 1}) \"{j['name']}\" by {j['artists'][0]['name']}")

# STEP 3 - GET CURRENT USERS LIBRARY AND COMPARE WITH RECOMMENDED TRACKS SET TO FILTER OUT SONGS USER ALREADY HAS

library_scope = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                          client_secret=client_secret,
                                                          scope='user-library-read',
                                                          redirect_uri=redirect_uri))
tracks_list = []


# LOOP TO GET AROUND THE LIMIT ON AMOUNT OF TRACKS RETRIEVED FROM LIBRARY
def show_tracks(results):
    for item1 in results['items']:
        track_uri = item1['track']
        tracks_list.append(track_uri['uri'])


results = library_scope.current_user_saved_tracks()
show_tracks(results)

while results['next']:
    results = library_scope.next(results)
    show_tracks(results)

# SET OF ALL USERS TRACKS
tracks_set = set(tracks_list)
print("Tracks in user library: " + str(len(tracks_set)))

# FILTER OUT ANY RECOMMENDED SONGS THAT THE USER ALREADY HAS
uris_to_set = set(uris_list)
uri = list(uris_to_set.difference(tracks_set))
print("Recommended tracks: " + str(len(uris_to_set)))
print("Recommended tracks user already has: " + str(len(uris_to_set) - len(uri)))

# SETTING MAX PLAYLIST LENGTH
if len(uri) > max_playlist_len:
    random.shuffle(uri)
    uri = uri[:75]
else:
    uri = uri

# STEP 4 - CREATE PLAYLIST

# USER PROMPT TO GET NEW TOKEN (next steps require a token that has been authenticated by the user)
webpage_for_token = f"https://developer.spotify.com/console/post-playlists/"
# in redirect site copy the "OAuth Token" in
# the box to the left of the green "Get Token" button
print("Go here and grab token: " + webpage_for_token)
token_input = input("Enter token: ")
print("Enter token: " + token_input)
print(token_input)
token2 = token_input

# PLAYLIST CREATION
playlist_endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
request_body = json.dumps({
    "name": playlist_name,
    "description": str(datetime.datetime.now()),
    "public": False
})
response = requests.post(url=playlist_endpoint, data=request_body, headers={"Content-Type": "application/json",
                                                                            "Authorization": f"Bearer {token2}"})

url = response.json()['external_urls']['spotify']

# STEP 5 - ADD SONGS TO THE PLAYLIST

playlist_id = response.json()['id']
add_songs = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
request_body = json.dumps({
    "uris": uri
})
response = requests.post(url=add_songs, data=request_body, headers={"Content-Type": "application/json",
                                                                    "Authorization": f"Bearer {token2}"})

print(f'Your playlist is ready at {url}')

```
