from typing import List, TypedDict, Optional

import discord.ext.commands
from discord import VoiceClient
from discord_slash import SlashContext

from dataFunc import get_title
from utils import start_playing_song, run_async


class Song(TypedDict):
    title: str
    query: str
    url: Optional[str]
    thumbnail: Optional[str]


class GuildSession:
    def __init__(self, guild_id: int, voice_client: discord.VoiceClient, channel_id: int, bot: discord.ext.commands.Bot,
                 queue: List[Song] = None):
        self.guild_id = guild_id
        self.voice_client: VoiceClient = voice_client
        self.channel_id = channel_id
        self._queue: List[Song] = queue if queue else []
        self._current_song: Optional[Song] = None
        self._prev_song: Optional[Song] = None
        self.bot = bot
        self._stop = False

    def queue_empty(self):
        return len(self._queue) == 0

    def add_to_queue(self, song: str, ctx: SlashContext):
        try:
            title = get_title(song)
            if len(self._queue) == 0 and not self._current_song:
                run_async(ctx.reply(f"Playing {title}", delete_after=1), client=self.bot)
                self._queue.append(Song(title=title, query=song, url=None, thumbnail=None))
            else:
                self._queue.append(Song(title=title, query=song, url=None, thumbnail=None))
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
                self._current_song = None
                self._stop = False
                return

            if self.voice_client.is_paused() and not force:
                self.voice_client.resume()
                return True

            self._next_song()
            if not self._current_song:
                self.voice_client.stop()
                return False

            url, video_link = start_playing_song(self._current_song.get('title'), self.voice_client, self.callback)
            run_async(self.bot.get_channel(self.channel_id).send(f"Now playing: {video_link}"), self.bot)

            return True
        return False

    def _next_song(self):
        self._prev_song = self._current_song
        if self._queue:
            self._current_song = self._queue.pop(0)
        else:
            self._current_song = None

    def skip_song(self, ctx: SlashContext):
        if self.voice_client.is_playing():
            self.voice_client.stop()
        else:
            run_async(ctx.reply("Nothing is playing"), self.bot)

    def callback(self, error, *args):
        if error:
            print(error, "please help me")
            self.bot.get_channel(self.channel_id).send(f"Error: {error}")
        else:
            self.start_playing()

    def get_titles(self):
        return [x.get('title') for x in self._queue]

    def clear_queue(self):
        self._queue = []

    def previous_song(self, ctx: SlashContext):
        if self._prev_song:
            self._queue.insert(0, self._prev_song)
            self._prev_song = self._current_song

            if self.voice_client.is_playing():
                self.voice_client.stop()
            else:
                self.start_playing()

            run_async(ctx.reply("Previous song played", delete_after=1), self.bot)
        else:
            run_async(ctx.reply("No previous song"), self.bot)

    def restart_song(self, ctx: SlashContext):
        if self._current_song:
            self._queue.insert(0, self._current_song)
            self._current_song = self._prev_song
            self.start_playing()
            run_async(ctx.reply("Restarted song", delete_after=1), self.bot)
        else:
            run_async(ctx.reply("No song playing"), self.bot)


class GuildSessionManager:
    def __init__(self, bot):
        self.sessions = {}
        self._bot = bot

    def create_session(self, guild_id, voice_client, channel_id, queue: List[Song], overwrite=False) -> (
            bool, GuildSession):
        if guild_id in self.sessions and not overwrite:
            self.sessions[guild_id].voice_client = voice_client
            self.sessions[guild_id].channel_id = channel_id
            return False, self.sessions[guild_id]
        session = self.sessions[guild_id] = GuildSession(guild_id, voice_client, channel_id, self._bot, queue)
        return True, session

    def get_session(self, guild_id) -> GuildSession:
        return self.sessions[guild_id]

    def remove_session(self, guild_id):
        if guild_id in self.sessions:
            del self.sessions[guild_id]
