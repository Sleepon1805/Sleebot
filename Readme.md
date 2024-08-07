This is a simple discord bot, that plays audio from youtube in a voice channel. It uses the discord.py library and youtube-dl to download the audio from youtube.

Code in this repo requires .env file with the following variables:
```
DISCORD_TOKEN=""
DOCKER_USER=""
DOCKER_PW=""
SPOTIPY_CLIENT_ID=""
SPOTIPY_CLIENT_SECRET=""
SPOTIPY_REDIRECT_URI=""
```

Current list of commands (/help):
```
0. /server_info | !server_info
Prints details of server
1. /raise_exception | !raise_exception
Raise and print an exception
e (string): Error message
2. /invite_link | !invite_link
Prints the invitation link for the bot
3. /timer | !timer
Start a timer
seconds (integer): Number of seconds to count down
event_name (string): Name of the event to count down to
4. /help | !help
Show help menu
5. /play | !play
Request a song by YouTube search or URL.
query (string): Search query or YouTube URL (video or playlist)
6. /spotify | !spotify
Make a spotify search and add YT songs to the queue.
category (string): Category to search for
search (string): Search query. Only exact matches are processed.
limit (integer): Numer of songs to add to the queue
7. /recs | !recs
Requests a spotify recommendations by artist.
artist (string): Search query. Only exact matches are processed.
limit (integer): Numer of songs to add to the queue
8. /pause | !pause
Pause the current song.
9. /resume | !resume
Resume if paused.
10. /skip | !skip
Skip the current song.
11. /stop | !stop
Stop and empty the queue.
12. /restart | !restart
Save the queue and restart the player
13. /queue | !queue
Show a queue of upcoming songs.
14. /shuffle | !shuffle
Shuffle the queue.
15. /change_volume | !change_volume
Change the player volume.
volume (number): Percentage value between 1 and 100
16. /status | !status
Prints some status information
```

TODO:
- Update logging: can not read from file with ```cat``` once it's too long
- Add 'random' command group
- Save last used commands and allow to repeat them
- Add !run_tests command
- Add pagination and button control to embed queue