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
PREFIX = config['PREFIX']

bot = Bot(command_prefix=PREFIX)
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
             options=[{"name": "song", "description": "Song Name or Link", "required": True, "type": 3}])
async def play_song(ctx: SlashContext, song: str = None):
    voice_client: VoiceClient = ctx.author.voice
    voice: VoiceClient = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client:
        channel: VoiceChannel = voice_client.channel
        if not voice:
            await channel.connect()
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
        if session.queue_empty() and not song:
            await ctx.reply('No song specified')
        else:
            await ctx.defer()
            if song:
                session.add_to_queue(song, ctx)
            session.start_playing()
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='leave', guild_ids=guild_ids)
async def leave_voice_channel(ctx: SlashContext):
    voice_client: VoiceClient = ctx.author.voice
    if voice_client:
        await voice_client.channel.disconnect()
        sessionManager.remove_session(ctx.guild.id)
        await ctx.send('Left voice channel')
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
    voice: VoiceClient = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_paused():
            voice.resume()
            await ctx.send('Song resumed')
        elif voice.is_playing():
            await ctx.send('Song is already playing')
        else:
            _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
            if session.queue_empty():
                await ctx.reply('No song in queue')
            else:
                await ctx.reply('Starting song', delete_after=1)
                session.start_playing()
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='stop', guild_ids=guild_ids)
async def stop_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_playing():
            _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
            session.stop()
            await ctx.send('Song stopped')
        else:
            await ctx.send('Song is not playing')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='skip', guild_ids=guild_ids)
async def skip_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
        session.skip_song(ctx)
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='queue', guild_ids=guild_ids)
async def queue_list(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
        titles = session.get_titles()
        formatted_titles = "\n".join([f'{i + 1}. {titles[i]}' for i in range(len(titles))])
        await ctx.reply(f'```{formatted_titles}```')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='clear', guild_ids=guild_ids)
async def clear_queue(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
        session.clear_queue()
        await ctx.reply('Queue cleared')
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='previous', guild_ids=guild_ids)
async def previous_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
        session.previous_song(ctx)
    else:
        await ctx.send('You are not in a voice channel')


@slash.slash(name='restart', guild_ids=guild_ids)
async def restart_song(ctx: SlashContext):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        _, session = sessionManager.create_session(ctx.guild.id, voice, ctx.channel_id, [])
        session.restart_song(ctx)
    else:
        await ctx.send('You are not in a voice channel')


bot.run(os.getenv('TOKEN'))
