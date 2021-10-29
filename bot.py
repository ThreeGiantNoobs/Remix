import json
import os

import discord
import dotenv
from discord import VoiceChannel, VoiceClient
from discord.ext.commands import Bot
from discord_slash import SlashCommand, SlashContext

from GuildSession import GuildSessionManager

dotenv.load_dotenv()

with open('config.json') as config_file:
    config = json.load(config_file)

guild_ids = config['SERVERS']

bot = Bot(command_prefix='!')
slash = SlashCommand(bot, sync_commands=True)

sessionManager = GuildSessionManager(bot)


@bot.event
async def on_ready():
    await bot.get_channel(id=837582224361652237).send('Bot is online')


@slash.slash(name='join', guild_ids=guild_ids)
async def join_voice_channel(ctx: SlashContext):
    voice_client: VoiceClient = ctx.author.voice
    if voice_client:
        await voice_client.channel.connect()
        sessionManager.create_session(ctx.guild.id, voice_client, ctx.channel_id, [])
        await ctx.send(f'Joined {voice_client.channel.name}')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='play', guild_ids=guild_ids,
             options=[{"name": "song", "description": "Song Name or Link", "required": "true", "type": 3}])
async def play_song(ctx: SlashContext, song: str):
    query = song
    voice_client: VoiceClient = ctx.author.voice
    voice: VoiceClient = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        channel: VoiceChannel = voice_client.channel
        if not voice:
            await channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        session = sessionManager.get_or_create_session(ctx.guild.id, voice, ctx.channel_id, [])
        session.add_to_queue(query, ctx)
        session.start_playing()
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
        session = sessionManager.get_or_create_session(ctx.guild.id, voice, ctx.channel_id, [])
        session.skip_song(ctx)
    else:
        await ctx.send('You are not in a voice channel')


bot.run(os.getenv('TOKEN'))
