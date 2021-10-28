import os
import re

import discord
import dotenv
import requests
import youtube_dl
from discord import VoiceChannel, VoiceClient
from discord.ext.commands import Bot
from discord_slash import SlashCommand, SlashContext

dotenv.load_dotenv()
guild_ids = [765583273854107658, 582073099588206602, 815786691394535425]
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True}
yt_link_pat = re.compile(r'(?:https?://)?(?:www\.)?youtu(?:be)?\.(?:com|be)(?:/watch/?\?v=|/embed/|/shorts/|/)(\w+)')
spotify_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/track/(\w+)')

queue = {}


def search(query):
    query = get_url(query)
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        response = ydl.extract_info(f"ytsearch: {query}", download=False)['entries'][0]
        video_url, video = response['url'], response['webpage_url']
    return video_url, video


def get_spotify_title(spotify_track_id):
    spotify_url = f'https://open.spotify.com/track/{spotify_track_id}'
    response = requests.get(spotify_url)
    title = re.search(r'<title>(.*?)</title>', response.text).group(1)
    return title


def get_url(url):
    match = re.match(yt_link_pat, url)
    spotify_match = re.match(spotify_pattern, url)
    if match:
        return match[1]
    elif spotify_match:
        return get_spotify_title(spotify_match[1])
    else:
        return url


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
                url, video_link = search(query)
                # ydl = Popen(['youtube-dl', '-f', 'bestaudio', '-g', url], stdout=PIPE, stderr=PIPE)
                voice.play(discord.FFmpegPCMAudio(url))
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.5
                await ctx.send(f'Playing song\n{video_link}')
        else:
            if not queue.get(f'{ctx.guild.id}'):
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


bot.run(os.getenv('TOKEN'))
