import os
import json

import discord
import dotenv
import asyncio
from discord import VoiceChannel, VoiceClient
from discord.ext.commands import Bot
from discord_slash import SlashCommand, SlashContext

from dataFunc import *

dotenv.load_dotenv()

with open('config.json') as config_file:
    config = json.load(config_file)

guild_ids = config['SERVERS']

queue = {}


class Arbitrary:
    def __init__(self, voice: VoiceClient, channel):
        self.voice = voice
        self.channel = channel
    
    def callback(self, *args):
        print(queue)
        if queue.get(self.voice.guild.id):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_queue(self))
        else:
            self.voice.stop()


async def run_queue(arbitary: Arbitrary):
    voice = arbitary.voice
    channel = arbitary.channel
    
    if queue.get(voice.guild.id):
        query = queue[voice.guild.id].pop(0)
        url, video_link = search(query)
        
        voice.play(discord.FFmpegPCMAudio(url), after=arbitary.callback)
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.5
        await channel.send(f'Now Playing: {video_link}')


bot = Bot(command_prefix='!')
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_ready():
    await bot.get_channel(id=837582224361652237).send('Bot is online')


@slash.slash(name='join', guild_ids=guild_ids)
async def join_voice_channel(ctx: SlashContext):
    channel: VoiceClient = ctx.author.voice
    if channel:
        await channel.channel.connect()
        await ctx.send(f'Joined {channel.channel.name}')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='play', guild_ids=guild_ids,
             options=[{"name": "song", "description": "Song Name or Link", "required": "true", "type": 3}])
async def play_song(ctx: SlashContext, song: str):
    query = song
    channel: VoiceClient = ctx.author.voice
    voice: VoiceClient = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if channel:
        channel: VoiceChannel = channel.channel
        if not voice:
            await channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        await ctx.defer()
        if not voice.is_playing():
            if not queue.get(ctx.guild.id):
                await ctx.reply(f'Playing song', hidden=True)
                queue[ctx.guild.id] = [query]
                await run_queue(Arbitrary(voice, ctx.channel))
        else:
            if not queue.get(ctx.guild.id):
                queue[ctx.guild.id] = [query]
            else:
                queue[ctx.guild.id].append(query)
            video = search(query)[1]
            await ctx.send(f'Song added to queue \n{video}')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='leave', guild_ids=guild_ids)
async def leave_voice_channel(ctx: SlashContext):
    channel = ctx.author.voice
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if channel:
        if voice:
            await voice.disconnect()
            await ctx.send('Disconnected')
        else:
            await ctx.send('You are not in a voice channel')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='pause', guild_ids=guild_ids)
async def pause_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_playing():
            voice.pause()
            await ctx.send('Song paused')
        else:
            await ctx.send('Song is not playing')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='resume', guild_ids=guild_ids)
async def resume_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_paused():
            voice.resume()
            await ctx.send('Song resumed')
        else:
            await ctx.send('Song is not paused')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='stop', guild_ids=guild_ids)
async def stop_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_playing():
            voice.stop()
            await ctx.send('Song stopped')
        else:
            await ctx.send('Song is not playing')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='skip', guild_ids=guild_ids)
async def skip_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_playing():
            voice.stop()
            await ctx.send('Song skipped')
            await run_queue(Arbitrary(voice, ctx.channel))
        else:
            await ctx.send('Song is not playing')
    else:
        await ctx.send('You are not in a voice channel')


bot.run(os.getenv('TOKEN'))
