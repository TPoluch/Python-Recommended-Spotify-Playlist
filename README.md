# Generate Customized Recommended Playlist

This python script generates a playlist tailored to the users music tastes.

# How it works:

1. Reads in the top n songs listened to by the user over 3 time spans - short-term, medium-term, long-term (assigns a rank 1-n based on most-least listened too for each time span)
Pulls the audio features (energy, danceability, loudness, etc) for each track
Assigns a weight to each track:
Weights are based on 2 factors:
Tracks are given a weight for their timespan (long-term being weighted highest and short-term lowest) 
They are also weighted based on the rank they have within their respective time-span
Calculates the target value for each audio feature using the weighted averages of the tracks
2. Pulls in all songs currently in the users library
3. Gets recommended songs based on the genres entered by the user and the target audio feature values established earlier
User can choose the minimum release year they want the recommended tracks to have 
4. Compares list of recommended songs to the songs currently in the users library and excludes any that the user already has
5. Creates playlist
6. Populates playlist
