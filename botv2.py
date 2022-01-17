import os
import json

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
            print(e)


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
        if e.__getattribute__("message"):
            await ctx.reply(e.message)
        else:
            print(e)


if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
