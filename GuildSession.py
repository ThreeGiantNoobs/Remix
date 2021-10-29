import asyncio
from typing import List, Tuple

import discord.ext.commands
from discord import VoiceClient
from discord_slash import SlashContext

from dataFunc import search, get_title
from utils import start_playing_song, run_async


class GuildSession:
    def __init__(self, guild_id: int, voice_client: discord.VoiceClient, channel_id: int, bot: discord.ext.commands.Bot,
                 queue: List[Tuple[str, str]] = None):
        self.guild_id = guild_id
        self.voice_client: VoiceClient = voice_client
        self.channel_id = channel_id
        self._queue = queue
        self.current_song = None
        self.bot = bot
        self._stop = False
    
    def queue_empty(self):
        return len(self._queue) == 0
    
    def add_to_queue(self, song: str, ctx: SlashContext):
        try:
            title = get_title(song)
            if len(self._queue) == 0 and not self.current_song:
                run_async(ctx.reply(f"Playing {title}", delete_after=1), client=self.bot)
                self._queue.append((song, title))
            else:
                self._queue.append((song, title))
                run_async(ctx.reply(f"Added {title} to queue"), client=self.bot)
        except IndexError as e:
            print(e)
            run_async(ctx.reply(f"No Results Found"), client=self.bot)
    
    def stop(self):
        self._stop = True
        self.voice_client.stop()
    
    def start_playing(self, force=False):
        if not self.voice_client.is_playing():
            if self._stop:
                self.current_song = None
                self._stop = False
                return
            
            if self.voice_client.is_paused() and not force:
                self.voice_client.resume()
                return True
            # if stop:
            #     self.voice_client.cleanup()
            self.current_song = self._queue.pop(0)[0] if self._queue else None
            if not self.current_song:
                # run_async(self.bot.get_channel(self.channel_id).send(f"Queue: Empty"), self.bot)
                return False
            url, video_link = start_playing_song(self.current_song, self.voice_client, self.callback)
            run_async(self.bot.get_channel(self.channel_id).send(f"Now playing: {video_link}"), self.bot)
            return True
        return False
    
    def skip_song(self, ctx: SlashContext):
        self.voice_client.stop()
        run_async(ctx.reply("Song skipped"), self.bot)
    
    def callback(self, error, *args):
        if error:
            print(error, "please help me")
            self.bot.get_channel(self.channel_id).send(f"Error: {error}")
        else:
            self.start_playing()
    
    def get_titles(self):
        return [x[1] for x in self._queue]


class GuildSessionManager:
    def __init__(self, bot):
        self.sessions = {}
        self._bot = bot
    
    def create_session(self, guild_id, voice_client, channel_id, queue: List[str], overwrite=False):
        if guild_id in self.sessions and not overwrite:
            self.sessions[guild_id].voice_client = voice_client
            self.sessions[guild_id].channel_id = channel_id
            return False
        self.sessions[guild_id] = GuildSession(guild_id, voice_client, channel_id, self._bot, queue)
        return True
    
    def get_session(self, guild_id) -> GuildSession:
        return self.sessions[guild_id]
    
    def get_or_create_session(self, guild_id, voice_client, channel_id, queue: List[str]) -> GuildSession:
        if guild_id in self.sessions:
            return self.sessions[guild_id]
        else:
            self.create_session(guild_id, voice_client, channel_id, queue)
            return self.sessions[guild_id]
    
    def remove_session(self, guild_id):
        del self.sessions[guild_id]
