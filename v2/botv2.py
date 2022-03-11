import os
import json
import traceback

import discord
import dotenv
from discord import VoiceChannel, VoiceClient
from discord.ext.commands import Bot
from discord_slash import SlashCommand, SlashContext

from Player import PlayerManager
from Exceptions import *

dotenv.load_dotenv()

with open('config.json') as config_file:
    config = json.load(config_file)

guild_ids = config['SERVERS']
log_channel = config['LOG_CHANNEL']
PREFIX = config['PREFIX']

bot = Bot(command_prefix=PREFIX)
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
        
        player = player_manager.get_or_create_player(voice.channel.guild.id)
        
        await player.join_voice_channel(ctx, force)
        await ctx.reply(f"Joined {voice.channel.name}")
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
        await ctx.reply(f"Left {voice.channel.name}")
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            traceback.print_exc()
            
            
@slash.slash(name="play", guild_ids=guild_ids,
             description="Plays a song from YouTube",
             options=[{"name": "query",
                       "description": "The query to search for",
                       "required": False, "type": 1}])
async def play(ctx: SlashContext, query: str = None):
    try:
        voice: VoiceClient = ctx.author.voice
        if not voice:
            raise AuthorVoiceException(ctx.author.mention)
        
        player = player_manager.get_or_create_player(voice.channel.guild.id)
        
        title, url, played = await player.play_song(ctx, query)
        if played:
            await ctx.reply(f"Now playing: {title}\n{url}")
        else:
            await ctx.reply(f"Queued: {title} ")
    except Exception as e:
        try:
            await ctx.reply(e.message)
        except AttributeError:
            print(traceback.print_exc())
            

@bot.event
async def on_song_end(player, session):
    ...

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
