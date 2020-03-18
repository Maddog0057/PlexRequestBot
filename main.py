import discord
import omdb
import requests
import json
import os
import sys
import asyncio
import time
import datetime
import logging
from logging.handlers import RotatingFileHandler
from discord.ext import commands

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

logDir = config["system"]["log"]
logFile = logDir+config["discord"]["name"]+".log"


class StreamToLogger(object):

   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''

   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())

   def flush(self):
      pass

handler = RotatingFileHandler(logFile,"a",maxBytes=1048576,backupCount=5)

logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
   handlers = [ handler ]
)


stdout_logger = logging.getLogger('STDOUT')
sl = StreamToLogger(stdout_logger, logging.INFO)
sys.stdout = sl

stderr_logger = logging.getLogger('STDERR')
sl = StreamToLogger(stderr_logger, logging.ERROR)
sys.stderr = sl


url = config["radarr"]["url"]
api = config["radarr"]["token"]
bot = commands.Bot(command_prefix='!')
bot.remove_command('help')
#channel = config["discord"]["channel"]
omdb.set_default('apikey', config["omdb"]["token"])

#@bot.check
async def is_channel(ctx):
	print(ctx.channel)
	return ctx.channel is str("plex_requests")

def verify(imdbid, number):
    embed = discord.Embed(Title="IMDb Search", description="Number "+str(number)+" selected", color=0x53f442)
    res = omdb.get(imdbid=str(imdbid), fullplot=False)
    embed.add_field(name= str(number)+": "+res['title']+", "+str(res['year']), value=res['plot'])
    return embed

def find(mtitle, count):
    query = omdb.search(mtitle) 
    fincount = int(count)+2
    print('finalcount is ', fincount)
    data = dict()
    count = int(count)
    while True:
        try:
                res=query[count]
        except:
	        errormsg() 
        try:
                res = omdb.get(imdbid=str(res['imdb_id']), fullplot=False)
        except:
                errormsg()
        data.update({int(count):res['imdb_id']})
        count+= 1
        if(count > fincount):
            break
    return data

async def scanmov(ctx, mid):
    print(mid)
    method = str("/command/?")
    lurl = (url+method+"apikey="+api)
    payload = dict()
    payload.update({'name':'MoviesSearch','movieIds':[int(mid)]})
    headers = {'content-type': 'application/json'}
    payload = json.dumps(payload)
    response = requests.post(lurl, data=payload, headers=headers)
    print(response.text)
    jsp = json.loads(response.text)
    print(jsp['id'])
    await ctx.send("```Searching...```")
    while True:
        method = str("/command/"+str(jsp['id'])+"/?")
        murl = (url+method+"apikey="+api)
        res = requests.get(murl) 
        print(res.text)
        res = json.loads(res.text)
        status = res['status']
        print("status is "+status)
        time.sleep(15)
        if status in ('failed', 'completed'):
            await ctx.send("```Finished!```")
            break

def format(data, mtitle, count):
    if(count < 3):
        place = str("top")
    else:
        place = str("next")
    embed = discord.Embed(Title="IMDb Search", description="Here are the "+place+" three results for "+mtitle+":", color=0x53f442)
    finalcount = int(count)+2
    while True:
        res = data[int(count)]
        resno = int(count)+1
        res = omdb.get(imdbid=str(res), fullplot=False)
        embed.add_field(name= str(resno)+": "+res['title']+", "+str(res['year']), value=res['plot'])
        count+=1
        if(count > finalcount):
            break
    return embed

async def checkMovie(imdbid, ctx):
    method = str("/movie/?")
    lurl = (url+method+"apikey="+api)
    response = requests.get(lurl)
    print(imdbid)
    if imdbid in response.text:
        mthd = str("/movie/lookup/imdb?imdbId="+imdbid+"&")
        furl = (url+mthd+"apikey="+api)
        res = requests.get(furl)
        item = json.loads(str(res.text))
        print(item)
        print(imdbid)
        embed = discord.Embed(Title="ITEM EXISTS", description="This Movie is already in your library: ", color=0x53f442)
        embed.add_field(name= item['title']+", "+str(item['year'])+", "+imdbid, value=str(item['overview']))
        await ctx.send(embed=embed)
        return str("have")
    else:
        print("NOTMATCH")
        return str("missing")

async def getMovie(imdbid, ctx):
    method = str("/movie/lookup/imdb?imdbId="+imdbid+"&")
    lurl = str(url+method+"apikey="+api)
    response = requests.get(lurl)
    res = json.loads(str(response.text))
    overview = str(res['overview'])
    payload = dict()
    payload.update({
        "title":res['title'],
        "year":res['year'],
        "qualityProfileId":"1",
        "titleSlug":res['titleSlug'],
        "images":res['images'],
        "tmdbId":res['tmdbId'],
        "rootFolderPath":config["radarr"]["path"],
        "monitored":True})
    payload = json.dumps(payload)
    #payload = json.loads(payload)
    method = str("/movie/?")
    lurl = str(url+method+"apikey="+api)
    print(lurl)
    print(payload)
    headers = {'content-type': 'application/json'}
    response = requests.post(lurl, data=payload, headers=headers)
    print(str(response.text))
    item = json.loads(str(response.text))
    await scanmov(ctx, item['id'])
    embed = discord.Embed(Title="ITEM REQUESTED", description="The following movie has been requested: ", color=0x53f442)
    embed.add_field(name= str(item['title'])+", "+str(res['year'])+", "+str(imdbid), value=str(overview))
    return embed

async def choice(ctx, ids, inmsg, embed, count):
    await ctx.send('Reply with the number of your selection, or the next number in the sequence for three more results')
    reply = await bot.wait_for('message', check=is_channel)
    print(reply.content)
    ch = int(reply.content)-1
    if(int(ch) > len(ids)):
        while True:
            count+=3
            ids = find(inmsg, count)
            embed = format(ids, inmsg, count)
            await ctx.send(embed=embed)
            await ctx.send('Reply with the number of your selection, or the next number in the sequence for three more results')
            reply = await bot.wait_for('message')
            if(int(ch) > len(ids)):
                True
            else:
                False
    else:
        selection = str(ids[int(ch)])
        verify(selection, int(ch))
        valid = await checkMovie(selection, ctx)
        asyncio.sleep(1)
        print("VALID= "+valid)
        if valid is 'missing':
            nembed = await getMovie(selection, ctx)
            await ctx.send(embed=nembed)

@bot.event
async def on_ready():
    print("/n"+"DateStamp: "+datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    print('Logged in as '+bot.user.name)
    print(bot.user.id)
    print('----------------')

@bot.command()
async def search(ctx, inmsg):
    if 'and' in inmsg:
        inmsg = inmsg.replace('and', '&')
    ids = find(inmsg, 0)
    embed = format(ids, inmsg, 0)
    await ctx.send(embed=embed)
    embed = None

@bot.command()
async def get(ctx, inmsg):
    if 'and' in inmsg:
        inmsg = inmsg.replace('and', '&')
    ids = find(inmsg, 0)
    embed = format(ids, inmsg, 0)
    await ctx.send(embed=embed)
    await choice(ctx, ids, inmsg, embed, 0)

@bot.command()
async def delmov(ctx, mid):
    method = str("/movie/"+mid)
    lurl = (url+method+"/?apikey="+api)
    response = requests.delete(lurl)
    print(response.text)

@bot.command()
async def rescan(ctx):
    method = str("/command/?")
    lurl = (url+method+"apikey="+api)
    payload = dict()
    payload.update({'name':'MissingMoviesSearch'})
    headers = {'content-type': 'application/json'}
    payload = json.dumps(payload)
    response = requests.post(lurl, data=payload, headers=headers)
    print(response.text)
    jsp = json.loads(response.text)
    print(jsp['id'])
    await ctx.send("```Searching...```")
    #oldmessage = str("NONE")
    while True:
        method = str("/command/"+str(jsp['id'])+"/?")
        murl = (url+method+"apikey="+api)
        res = requests.get(murl) 
        print(res.text)
        res = json.loads(res.text)
        #message = res['message']
        status = res['status']
        #print("status is "+status)
        time.sleep(15)
        if status not in ('completed'):
            print("status is "+status)
            await ctx.send("```Still Searching```")
        if status in ('failed', 'completed'):
            await ctx.send("```"+status+"```")
            print("Search Completed")
            break

async def errormsg():
	channel = bot.get_channel(474291856038166530)
	await channel.send("``` Invalid Syntax! Ex: !get \"The Big Lebowski\" ```") 

@bot.command()
async def help(ctx):
    embed = discord.Embed(Title="Commands", description="Here are my commands: ", color=0x8C198C)
    embed.add_field(name= "!search <string> :", value="Searches for <string> and returns the top three results from IMDB. \nUSAGE: !search \"The Big Lebowski\" \n(NOTE: Multiword strings must be enclosed in quotes)")
    embed.add_field(name= "!get <string> :", value="Performs the same function as search but will prompt for a choice in movie to download to plex. \nUSAGE: !get \"totoro\"")
    embed.add_field(name= "!rescan :", value="Tells Radarr to scan for all items that have not been grabbed yet. \nUSAGE: !rescan")
    embed.add_field(name= "!help :", value="Displays this help message. \nUSAGE: !help")
    await ctx.send(embed=embed)

bot.run(config["discord"]["token"])

