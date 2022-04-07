import asyncio
from enum import Enum
from typing import Optional

import discord
from discord import VoiceClient, VoiceChannel, TextChannel, Guild, FFmpegPCMAudio
from discord.ext.commands import Bot
from discord_slash import SlashContext
from tenacity import retry, stop_after_attempt

from Exceptions import *
from SessionV2 import Session, SessionManager, Song
from dataFuncV2 import get_data

session_manager: SessionManager = SessionManager()


class Status(Enum):
    NOT_CONNECTED = 0
    PLAYING = 1
    PAUSED = 2
    STOPPED = 3


def update_player_wrapper(func):
    if asyncio.iscoroutinefunction(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            finally:
                args[0].voice_client = discord.utils.get(args[0].bot.voice_clients,
                                                         guild=args[0].guild)
                args[0].current_channel = args[0].voice_client.channel if args[0].voice_client else None
    else:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            finally:
                args[0].voice_client = discord.utils.get(args[0].bot.voice_clients,
                                                         guild=args[0].guild)
                args[0].current_channel = args[0].voice_client.channel if args[0].voice_client else None

    return wrapper


class Player:
    def __init__(self, guild_id: int, bot: Bot):
        self.bot: Bot = bot
        self.guild: Guild = bot.get_guild(guild_id)
        self.current_channel: Optional[VoiceChannel] = None
        self.text_channel: Optional[TextChannel] = None
        self.voice_client: Optional[VoiceClient] = discord.utils.get(self.bot.voice_clients, guild=self.guild)
        self.session: Optional[Session] = session_manager.get_or_create_session(self)
        self.dont_play_next = False

    def status(self):
        if not self.voice_client:
            return Status.NOT_CONNECTED
        elif self.voice_client.is_playing():
            return Status.PLAYING
        elif self.voice_client.is_paused():
            return Status.PAUSED
        else:
            return Status.STOPPED

    def update_player(self, ctx=None):
        if ctx:
            self.text_channel = ctx.channel
        self.voice_client = discord.utils.get(self.bot.voice_clients,
                                              guild=self.guild)
        self.current_channel = self.voice_client.channel if self.voice_client else None

    @update_player_wrapper
    async def join_voice_channel(self, ctx: SlashContext, force: bool):
        status = self.status()
        self.update_player(ctx)
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
        raise AlreadyConnectedException(self.bot.user.name, self.current_channel.mention)

    @update_player_wrapper
    async def leave_voice_channel(self, ctx: SlashContext):
        status = self.status()
        self.update_player(ctx)
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
    async def play_song(self, ctx: SlashContext = None, query: str = None):
        status = self.status()

        if not query and not ctx:
            session: Session = session_manager.get_or_create_session(self)
            session.remove_latest()
            song = session.current_song

            if not song:
                return None, False
        else:
            self.update_player(ctx)
            channel: VoiceChannel = ctx.author.voice.channel

            if status == Status.NOT_CONNECTED:
                await channel.connect()
                self.update_player(ctx)

            session: Session = session_manager.get_or_create_session(self)
            song: Song = session.queue_song(query)

        return song, session.queue[0] == song

    async def pause_song(self, ctx: SlashContext = None):
        status = self.status()
        self.update_player(ctx if ctx else None)

        if status == Status.NOT_CONNECTED:
            raise NotConnectedException(self.bot.user.name)
        if status != Status.PLAYING:
            raise NotPlayingException(self.bot.user.name)

        self.voice_client.pause()
        return True

    async def resume_song(self, ctx: SlashContext):
        status = self.status()
        self.update_player(ctx)

        if status == Status.NOT_CONNECTED:
            raise NotConnectedException(self.bot.user.name)
        if status == Status.PLAYING:
            raise AlreadyPlayingException(self.bot.user.name, self.current_channel.name)
        if status != Status.PAUSED:
            raise NotPausedException(self.bot.user.name)

        self.voice_client.resume()
        return True

    async def skip_song(self, ctx: SlashContext):
        status = self.status()
        self.update_player(ctx)

        if status == Status.NOT_CONNECTED:
            raise NotConnectedException(self.bot.user.name)
        if status == Status.STOPPED:
            raise AlreadyStoppedException(self.bot.user.name)

        self.voice_client.stop()
        return True

    async def stop_song(self, ctx: SlashContext):
        await self.skip_song(ctx)
        self.dont_play_next = True

    def _end_song(self, *args):
        print(args)
        self.bot.dispatch('song_end', self)

    @retry(stop=stop_after_attempt(3))
    @update_player_wrapper
    def run_song(self, song: Song):
        song = get_data(song.query, run=True)
        self.voice_client.play(FFmpegPCMAudio(song['video_dl_url']), after=self._end_song)
        self.voice_client.source = discord.PCMVolumeTransformer(self.voice_client.source)
        self.voice_client.source.volume = 0.5

    def stop_player(self):
        self.voice_client.stop()


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
