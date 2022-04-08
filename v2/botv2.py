import enum
import json
import os
import traceback

import discord
import dotenv
from discord import VoiceClient, Activity, ActivityType, Embed
from discord.ext.commands import Bot
from discord_slash import SlashCommand, SlashContext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option, create_choice

from Exceptions import *
from Player import PlayerManager

dotenv.load_dotenv()

with open('config.json') as config_file:
    config = json.load(config_file)

guild_ids = config['SERVERS']
log_channel = config['LOG_CHANNEL']
PREFIX = config['PREFIX']

activity = Activity(type=ActivityType.playing, name="with my life")

bot = Bot(command_prefix=PREFIX, help_command=None, activity=activity)
slash = SlashCommand(bot, sync_commands=True)

player_manager = PlayerManager(bot)


@bot.event
async def on_ready():
    await bot.get_channel(log_channel).send(f'<@{bot.user.id}> has connected to Discord!')


@slash.slash(name="join", guild_ids=guild_ids,
             options=[{"name": "force",
                       "description": "Join even if the bot is already in a voice channel",
                       "required": False, "type": 5}],
             description="Joins the voice channel you are in")
async def join(ctx: SlashContext, force: bool = False):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        await ctx.defer()
        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await player.join_voice_channel(ctx, force)

        embed = Embed(description=f"Joined {voice.channel.mention}")
        await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="leave", guild_ids=guild_ids,
             description="Leaves the voice channel you are in")
async def leave(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await player.leave_voice_channel(ctx)

        embed = Embed(description=f"Left {voice.channel.mention}")
        await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="play", guild_ids=guild_ids,
             description="Plays a song from YouTube",
             options=[{"name": "query",
                       "description": "The query to search for",
                       "required": False, "type": 3}])
async def play(ctx: SlashContext, query: str = None):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()

        if not query:
            await resume(ctx)
            return

        song, played = await player.play_song(ctx, query)
        if played:
            embed = discord.Embed(title=player.session.current_song.title, url=player.session.current_song.video_url)
            embed.set_author(name=player.session.current_song.artist)
            embed.set_thumbnail(url=player.session.current_song.thumbnail)
            await ctx.reply(embed=embed)
        else:
            embed = Embed(description=f"Added {song.title} to queue")
            await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="pause", guild_ids=guild_ids,
             description="Pauses the current song")
async def pause(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        await player.pause_song(ctx)

        embed = Embed(description=f"Paused {player.session.current_song.title}")
        await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="resume", guild_ids=guild_ids,
             description="Resumes the current song")
async def resume(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        await player.resume_song(ctx)

        embed = Embed(description=f"Resumed {player.session.current_song.title}")
        await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="skip", guild_ids=guild_ids,
             description="Skips the current song")
async def skip(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        await player.skip_song(ctx)

        embed = Embed(description=f"Skipped {player.session.current_song.title}")
        await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="stop", guild_ids=guild_ids,
             description="Stops the current song")
async def stop(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        await player.stop_song(ctx)

        embed = Embed(description=f"Stopped Remix")
        await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="queue", guild_ids=guild_ids,
             description="Shows the current queue")
async def queue(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        queue = player.session.queue
        if not queue:
            embed = Embed(description="Queue is empty")
            await ctx.reply(embed=embed)
            return

        embed = Embed(description="Queue")
        for i, song in enumerate(queue):
            embed.add_field(name=f'{i + 1}. {song.title}', value=song.artist)
        await ctx.reply(embed=embed)

    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="current", guild_ids=guild_ids,
             description="Shows the current song")
async def current(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        if player.session.current_song:
            embed = discord.Embed(title=player.session.current_song.title, url=player.session.current_song.video_url)
            embed.set_author(name=player.session.current_song.artist)
            embed.set_thumbnail(url=player.session.current_song.thumbnail)
            await ctx.reply(embed=embed)
        else:
            embed = discord.Embed(description="No song is playing")
            await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="shuffle", guild_ids=guild_ids,
             description="Toggles shuffle for the current queue")
async def shuffle(ctx: SlashContext):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        await player.toggle_shuffle(ctx)

        if player.session.shuffle:
            embed = Embed(description="Shuffle enabled")
            await ctx.reply(embed=embed)
        else:
            embed = Embed(description="Shuffle disabled")
            await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@slash.slash(name="loop", guild_ids=guild_ids,
             options=[
                 create_option(
                     name="loop_type",
                     description="Loop type",
                     option_type=SlashCommandOptionType.INTEGER,
                     required=False,
                     choices=[
                         create_choice(name="none", value=0),
                         create_choice(name="song", value=1),
                         create_choice(name="queue", value=2)
                     ]
                 )
             ],
             description="Toggles loop for the current queue")
async def loop(ctx: SlashContext, loop_type: int = -1):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)

        player = player_manager.get_or_create_player(voice.channel.guild.id)

        await ctx.defer()
        await player.set_loop(ctx, loop_type)

        if player.session.loop == 0:
            embed = Embed(description="Loop disabled")
        elif player.session.loop == 1:
            embed = Embed(description="Looping current song")
        elif player.session.loop == 2:
            embed = Embed(description="Looping queue")
        else:
            embed = Embed(description="Bro how tf?!")
        await ctx.reply(embed=embed)
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()


@bot.event
async def on_song_end(player):
    song, played = await player.play_song()
    if player.dont_play_next:
        try:
            await player.pause_song()
        except NotPlayingException:
            pass
        player.dont_play_next = False
    else:
        if played:
            embed = discord.Embed(title=player.session.current_song.title, url=player.session.current_song.video_url)
            embed.set_author(name=player.session.current_song.artist)
            embed.set_thumbnail(url=player.session.current_song.thumbnail)
            await player.text_channel.send(embed=embed)
        else:
            embed = Embed(description=f"Queue ended")
            await player.text_channel.send(embed=embed)


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
