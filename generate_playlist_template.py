import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import requests
import json
import datetime
import random
import pyinputplus

# MUST ADD SPOTIPY ENV VARIABLES
# SPOTIPY_CLIENT_ID: 'your_client_id'
# SPOTIPY_CLIENT_SECRET: 'your_client_secret'
# SPOTIPY_REDIRECT_URI: 'your_redirect_url'

# USER CREDENTIALS
client_id = 'your_client_id'
client_secret = 'your_client_secret'
redirect_uri = 'your_redirect_url'
user_id = "your_user_id"
archive_file = 'your_desktop_filepath'

# PREFERENCE VARIABLES
sample_size = 10  # number of songs from each time span (short,medium,long)
n_years = 5  # only add songs released within the  last n years
limit = 5  # number of recommended songs to pull for each seed track
max_playlist_len = 75

# RETRIEVE TOKEN FOR API CALLS THAT DON'T REQUIRE USER AUTHORIZATION
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

# VARIABLES
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               scope='user-top-read', redirect_uri=redirect_uri))
recommendations_url = "https://api.spotify.com/v1/recommendations?"
market = "US"
uris_list = []
list_one = []
release_date_min = datetime.datetime.now() - datetime.timedelta(days=n_years * 365)
ranges = ['short_term', 'medium_term', 'long_term']
username = user_id
input_playlist_id = ''
input_playlist_tracks = []
input_playlist_list = []
tracks_list = []
valid_input = False
input_playlist_name = str()

# STEP 1 - DECIDE BETWEEN HISTORIC DATA OR SPECIFIC PLAYLIST
print("Which source would you prefer the script use to build your music taste profile?" '\n'
      "A) Historic data" '\n'
      "B) Specific playlist")
input_source = pyinputplus.inputChoice((['A', 'B']), prompt="Please enter either A or B: ", caseSensitive=False)

# IF THEY CHOOSE PLAYLIST THEN ENTER PLAYLIST NAME SO WE CAN GET THE ID
if str(input_source) == "B" or str(input_source) == "b":
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope='playlist-read-private'))
    play_list = []
    results_play_test = sp.current_user_playlists(limit=50)
    for i, item in enumerate(results_play_test['items']):
        play_list.append(item['name'])
    while not valid_input:
        input_playlist_name = input("Enter playlist name: ")
        if str(input_playlist_name) in play_list:
            valid_input = True
        else:
            print("Invalid playlist name. Please try again")
    print("Fetching playlist...")
    playlists = sp.user_playlists(username)

    # GET PLAYLIST_ID
    for playlist in playlists['items']:
        if playlist['name'] == str(input_playlist_name):
            input_playlist_id = playlist['id']
            input_playlist_list.append(input_playlist_id)

            # GET PLAYLIST ITEMS
            ip_result = sp.playlist_items(input_playlist_id)

            # GET ALL THE TRACKS INFORMATION
            for i, item in enumerate(ip_result['items']):
                x = item['track']
                track_info = sp.track(x['id'])
                rank = i
                track_features = sp.audio_features(x['id'])
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
                list_one.append([rank, seed, acousticness, danceability, energy, loudness, speechiness,
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

# IF USING HISTORIC DATA
else:

    # LOOP THROUGH EACH TIME SPAN PULLING [sample_size] AMOUNT OF TRACKS AND THEIR DETAILS TO CREATE A LIST
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=client_secret,
                                                   scope='user-top-read', redirect_uri=redirect_uri))
    for sp_range in ranges:
        tt_result = sp.current_user_top_tracks(time_range=sp_range, limit=sample_size)
        for i, item in enumerate(tt_result['items']):
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

# STEP 3 - GET CURRENT USERS LIBRARY AND COMPARE WITH RECOMMENDED TRACKS SET TO FILTER OUT SONGS USER ALREADY HAS

if len(input_playlist_list) > 1:
    print(" " '\n'
          "********************** PLAYLIST NAME NOT UNIQUE *****************************" '\n'
          "-- " + str(len(input_playlist_list)) + " playlists used as source playlist --" '\n'
          "CAUSE: more than one playlists with the name " + "'" + input_playlist_name + "'" '\n'
          "FIX: rename one of them and try again" '\n'
          " " '\n'
          "links for the playlists are below: ")
    for e, input_index in enumerate(input_playlist_list):
        input_number = e + 1
        input_link = input_playlist_list[e]
        input_url = f'https://open.spotify.com/playlist/{input_link}'
        print(input_playlist_name+" ("+str(input_number)+") : "+input_url)
    exit()


else:
    print("Analyzing...")

library_scope = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                          client_secret=client_secret,
                                                          scope='user-library-read', redirect_uri=redirect_uri))
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

# CREATE SET OF ALL USERS TRACKS
tracks_set = set(tracks_list)
print("Tracks in user library: " + str(len(tracks_set)))
uris_to_set = set(uris_list)
archive_set = set()
uri_takeout_archive = set()
uri = []

print("Exclude songs that were recommended in previous executions?")
archive_activation = pyinputplus.inputYesNo(prompt="Please enter yes or no: ",yesVal='yes',noVal='no', caseSensitive=False)

if archive_activation == 'yes':
    archive_list = []
    archive_set = set()
    file_input = open(archive_file+"Old_Recommended_Tracks.txt", "r")
    for file_i in file_input:
        file_i.split('| ')
        archive_list.append(file_i)
    file_input.close()
    archive_set = set(archive_list)
    uri_takeout_archive = uris_to_set.difference(archive_set)
    uri = list(uri_takeout_archive.difference(tracks_set))

else:
    print("archive function not activated")
    uri = list(uris_to_set.difference(tracks_set))

# FILTER OUT ANY RECOMMENDED SONGS THAT THE USER ALREADY HAS
print("Recommended tracks: " + str(len(uris_to_set)))
print("Recommended tracks user already has: " + str(len(uris_to_set) - len(uri)))

# SETTING MAX PLAYLIST LENGTH
if len(uri) > max_playlist_len:
    random.shuffle(uri)
    uri = uri[:75]
else:
    uri = uri

# STEP 4 - CREATE PLAYLIST

# USER PROMPT TO GET NEW TOKEN (next steps need a token that requires user authentication)
webpage_for_token = f"https://developer.spotify.com/console/post-playlists/"

# in redirect site copy the "OAuth Token" in the box to the left of the green "Get Token" button
print("Go here and grab token: " + webpage_for_token)
token_input = input("Enter token: ")
token2 = token_input

# PLAYLIST CREATION
playlist_endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
playlist_name = input("Name your new playlist: ")
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

if archive_activation == 'yes':
    uri_archive_str = '| '.join(uri)
    f = open(archive_file+"Old_Recommended_Tracks.txt",
             "a")
    f.write(uri_archive_str)
    f.close()
    f2 = open(archive_file + playlist_name + '.txt', "x")
    f2.write(uri_archive_str)
    f2.close()
    print('Enjoy!')
else:
    uri_archive_str = '| '.join(uri)
    f2 = open(archive_file + playlist_name + '.txt', "x")
    f2.write(uri_archive_str)
    f2.close()
    print('Enjoy!')
