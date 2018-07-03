# PlexRequestBot
A discord bot to request for media on Plex

Currently this bot only has the ability to search IMDB and return the top 3 results for your search string.

## INSTALLATION GUIDE:

* (apt or yum) install python3 python3-pip
* pip3 install imdbpy requests
* python3 -m pip install -U https://github.com/Rapptz/discord.py/archive/rewrite.zip
* follow this [guide](https://twentysix26.github.io/Red-Docs/red_guide_bot_accounts/) to create a discord bot account
* cp config.json.sample config.json
* fill in the config with the necessary information
* python3 main.py
