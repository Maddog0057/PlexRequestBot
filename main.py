import discord
import imdb
import requests
import json
from discord.ext import commands

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

url = config["radarr"]["url"]
api = config["radarr"]["token"]
channel = config["discord"]["channel"]
bot = commands.Bot(command_prefix='!') 
ia = imdb.IMDb()    

def movierequest(mtitle, count):
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
        mid[count] = res.movieID
        ia.update(res, 'plot')
        plot =  str(res['plot'][0])
        plot = plot.split('.', 1)[0]
        embed.add_field(name= str(resno)+": "+res['title']+", "+str(res['year']), value=plot)
        count+=1
        if(count > finalcount):
            break
    return embed mid

def mediaget(media, mid):
    await 

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

@bot.command()
async def request(chx, media, search):
    count = 0
    mediaswitch = {
        "movie": movierequest(search, count),
        "tvseries": tvrequest(search, count),
        "music": musicrequest(search, count),
    }
    request = mediaswitch.get(media)
    embed = request(0)
    mid = request(1)
    await channel.send(embed=embed)
    response = await channel.wait_for_message()
    respswitch = {
        1: mediaget(media, mid[0]),
        2: mediaget(media, mid[1]),
        3: mediaget(media, mid[2]),
        'next': mediaswitch.get(media)
    }
    count+=3
    request = respswitch.get(response)







bot.run(config["discord"]["token"])