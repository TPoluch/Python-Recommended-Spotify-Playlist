# User-Unique Recommended Songs Playlist

This python script generates a playlist tailored to the users music tastes through use of Spotify's API. It deciphers the users music preferences through analysis of their favorite songs, audio feature tendencies, and other key factors. Automates the sign in process using webscraping (*uses the sign in with Facebook option so adjust lines 81-83 if needed*)

# How it works:

1. User inputs the requested values for:

    * What will act as the foundation for the script to build their preferences profile from - either historic data or a specific playlist
        * Historic Data: Reads the top 'n' tracks and their related details for tracks listened to by the user over 3 time spans - short-term, medium-term, long-term (assigns a rank to each track 1,2,3...n based on most-least listened to for each time span)
        * Playlist: User is prompted to enter the playlist name and then the the tracks within the playlist and their details are retrieved. There is a validation step built in to verify the users playlist name is actually a playlist within the users profile. If the user enters and incorrect playlist name then they will be prompted to retry. If they enter a playlist name and the script identifies they have 2 or more playlists with the same name then they will be notified, given links to each playlist, and asked to change the names and start over.

    * Whether or not they would like to exclude recommended songs from previous executions. If yes then the file archiving all recommended songs from past runs is read in and those songs are taken out of the current recommendation list.
    
    * What they want to name the new playlist

2. Webscraping is used to bypass the user authentication step needed to create a playlist. This piece operates by opening a webpage (the webpage is headless so nothing will show up on the screen, it will just operate in the background) and navigating to spotify dev. From there it requests a token for creating a public playlist. After that, a login widow is handled using the credentidials populated in the "Credentials" file and then the token populated on the following page is retrieved and stored for later use in the script

2. The data processing starts with using the parameters and inputs defined in step 1 to get a list of tracks to load into the script. Each track gets 'n' recommended tracks by using the track as a "seed track" and using its audio features (energy, danceability, loudness, etc) values as the target aduio feature values for the possible recommended songs. Data is then processed and recommended tracks are identified.

    * The amount of recommended tracks pulled can be changed by the user in the "preference variables" section. The user can also choose the max length for the playlist, the minimum release date for recommended tracks, etc.
    
3. Pulls in all tracks currently in the users library and compares it to the list of recommended tracks. Any recommended tracks that are already in the user's library are removed from the recommended list.
    
4. Creates and populates playlist
