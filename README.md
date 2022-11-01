# soundboard Discord Bot

## Usage:

- Create a ```token.txt``` file which contains your Discord API token.
- Run ```python main.py```.

## How it works:

- The bot only communicates via DMs.
- Send ```!new <sound name> <url>``` to create a sound.
- Send ```!play <sound name>``` to play the sound.
  - The bot must have permissions to join the voice channel you are currently in.
- Send ```!delete <sound name>``` to delete a sound.
- Send ```!list``` to list all of your sounds.

## Advantages of communication over DMs:

- Users all get their own unique soundboard tied to their discord account.
- Server owners can restrict the bot very easily by using native discord permissions.
- Doesn't clutter server.

## Limitations

- Only Youtube links work at the moment.
- Youtube shorts don't work ([youtubedl](https://github.com/ytdl-org/youtube-dl) limitation)
- Can't use share links with start time ([youtubedl](https://github.com/ytdl-org/youtube-dl) limitation)

## TODO (help appreciated):

1. Containerization - Create a docker image that can run the bot.
2. Enable YouTube shorts
3. Enable start times
