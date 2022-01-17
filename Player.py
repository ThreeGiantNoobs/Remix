from enum import Enum
from typing import Optional

import discord
from discord import VoiceClient, VoiceChannel
from discord.ext.commands import Bot
from discord_slash import SlashContext

from Exceptions import *


class Status(Enum):
    NOT_CONNECTED = 0
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


class Player:
    def __init__(self, guild_id: int, bot: Bot):
        self.bot: Bot = bot
        self.guild_id: int = guild_id
        self.current_channel: Optional[VoiceChannel] = None
        self.voice_client: Optional[VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=self.guild_id)
    
    def status(self):
        if not self.voice_client:
            return Status.NOT_CONNECTED
        elif self.voice_client.is_playing():
            return Status.PLAYING
        elif self.voice_client.is_paused():
            return Status.PAUSED
        else:
            return Status.STOPPED
    
    def update_player(self):
        self.voice_client: Optional[VoiceClient] = discord.utils.get(self.bot.voice_clients,
                                                                     guild=self.bot.get_guild(self.guild_id))
        self.current_channel = self.voice_client.channel if self.voice_client else None
    
    async def join_voice_channel(self, ctx: SlashContext, force: bool):
        try:
            self.update_player()
            status = self.status()
            channel: VoiceChannel = ctx.author.voice.channel
            
            if status == Status.NOT_CONNECTED:
                await channel.connect()
                return True
            if channel == self.current_channel:
                raise AlreadyConnectedException(self.bot.user.name, channel.mention)
            if force:
                if status != Status.STOPPED:
                    self.voice_client.stop()
                await self.voice_client.move_to(channel)
                return True
            return AlreadyConnectedException(self.bot.user.name, self.current_channel.mention)
        
        finally:
            self.update_player()
    
    async def leave_voice_channel(self, ctx: SlashContext):
        try:
            self.update_player()
            status = self.status()
            channel: VoiceChannel = ctx.author.voice.channel
            
            if status == Status.NOT_CONNECTED:
                raise NotConnectedException(self.bot.user.name)
            if channel != self.current_channel:
                raise NotConnectedException(self.bot.user.name, channel.mention)
            if status != Status.STOPPED:
                self.voice_client.stop()
            await self.voice_client.disconnect()
            return True
        
        finally:
            self.update_player()


class PlayerManager:
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.players: dict = {}
    
    def _create_player(self, guild_id: int):
        player = Player(guild_id, self.bot)
        self.players[guild_id] = player
        return player
    
    def _get_player(self, guild_id: int):
        player = self.players.get(guild_id)
        if not player:
            raise PlayerNotFoundException(self.bot.get_guild(guild_id).name)
        return player
    
    def get_or_create_player(self, guild_id: int):
        try:
            player = self._get_player(guild_id)
        except PlayerNotFoundException:
            player = self._create_player(guild_id)
        return player
