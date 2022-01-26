import asyncio
from enum import Enum
from typing import Optional

import discord
from discord import VoiceClient, VoiceChannel, Guild, FFmpegPCMAudio
from discord.ext.commands import Bot
from discord_slash import SlashContext

from Exceptions import *
from SessionV2 import Session, SessionManager, Song

session_manager: SessionManager = SessionManager()


class Status(Enum):
    NOT_CONNECTED = 0
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


class Player:
    def __init__(self, guild_id: int, bot: Bot):
        self.bot: Bot = bot
        self.guild: Guild = bot.get_guild(guild_id)
        self.current_channel: Optional[VoiceChannel] = None
        self.voice_client: Optional[VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=self.guild)
        self.session: Optional[Session] = session_manager.get_or_create_session(self)
    
    def status(self):
        if not self.voice_client:
            return Status.NOT_CONNECTED
        elif self.voice_client.is_playing():
            return Status.PLAYING
        elif self.voice_client.is_paused():
            return Status.PAUSED
        else:
            return Status.STOPPED
    
    def update_player_wrapper(func):
        if asyncio.iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                try:
                    await func(*args, **kwargs)
                finally:
                    args[0].voice_client = discord.utils.get(args[0].bot.voice_clients,
                                                             guild=args[0].guild)
                    args[0].current_channel = args[0].voice_client.channel if args[0].voice_client else None
        else:
            def wrapper(*args, **kwargs):
                try:
                    func(*args, **kwargs)
                finally:
                    args[0].voice_client = discord.utils.get(args[0].bot.voice_clients,
                                                             guild=args[0].guild)
                    args[0].current_channel = args[0].voice_client.channel if args[0].voice_client else None
        
        return wrapper
    
    def update_player(self):
        self.voice_client = discord.utils.get(self.bot.voice_clients,
                                              guild=self.guild)
        self.current_channel = self.voice_client.channel if self.voice_client else None
    
    @update_player_wrapper
    async def join_voice_channel(self, ctx: SlashContext, force: bool):
        status = self.status()
        self.update_player()
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
    
    @update_player_wrapper
    async def leave_voice_channel(self, ctx: SlashContext):
        status = self.status()
        self.update_player()
        channel: VoiceChannel = ctx.author.voice.channel
        
        if status == Status.NOT_CONNECTED:
            raise NotConnectedException(self.bot.user.name)
        if channel != self.current_channel:
            raise NotConnectedException(self.bot.user.name, channel.mention)
        if status != Status.STOPPED:
            self.voice_client.stop()
        await self.voice_client.disconnect()
        return True
    
    @update_player_wrapper
    async def play_song(self, ctx: SlashContext, query: str):
        status = self.status()
        channel: VoiceChannel = ctx.author.voice.guild
        
        if status == Status.NOT_CONNECTED:
            await channel.connect()
            self.update_player()
        
        if status == Status.STOPPED:
            song: Song = self.session.play_song(query)
            self.run_song(song.dl_url)
            return song.title, song.video_url
    
    @update_player_wrapper
    def run_song(self, url):
        self.voice_client.play(FFmpegPCMAudio(url), after=self.session.callback)
        self.voice_client.source = discord.PCMVolumeTransformer(self.voice_client.source)
        self.voice_client.source.volume = 0.5


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
    
    def get_or_create_player(self, guild_id: int) -> Player:
        try:
            return self._get_player(guild_id)
        except PlayerNotFoundException:
            return self._create_player(guild_id)
