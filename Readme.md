This is a simple discord bot, that plays audio from youtube links in a voice channel. It uses the discord.py library and youtube-dl to download the audio from youtube.

Code in this repo requires .env file with the following variables:
```
DISCORD_TOKEN=""
DOCKER_USER=""
DOCKER_PW=""
SPOTIPY_CLIENT_ID=""
SPOTIPY_CLIENT_SECRET=""
SPOTIPY_REDIRECT_URI=""
```

TODO:
- Rename /help_msg to /help
- Fix issue with expired message links
- Add standard (voice channel) check for all commands