import discord
import imdb
import requests
import json
from discord.ext import commands

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

url = config["radarr"]["url"]
api = config["radarr"]["token"]
bot = commands.Bot(command_prefix='!') 
ia = imdb.IMDb()

def format(mtitle, count):
    query = ia.search_movie(mtitle)
    if(count < 3):
        place = str("top")
    else:
        place = str("next")
    embed = discord.Embed(Title="IMDb Search", description="Here are the "+place+" three results for "+mtitle, color=0x53f442)
    finalcount = int(count)+2
    while True:
        res=query[int(count)]
        resno = int(count)+1
        ia.update(res, 'plot')
        plot =  str(res['plot'][0])
        plot = plot.split('.', 1)[0]
        embed.add_field(name= str(resno)+": "+res['title']+", "+str(res['year']), value=plot)
        count+=1
        if(count > finalcount):
            break
    return embed

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def search(channel, inmsg):
    embed = format(inmsg, 0)
    await channel.send(embed=embed)
    embed = None


bot.run(config["discord"]["token"])