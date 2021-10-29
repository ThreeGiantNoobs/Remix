import discord.ext.commands
from discord import VoiceClient
from discord_slash import SlashContext

from dataFunc import search
from utils import start_playing_song


class GuildSession:
    def __init__(self, guild_id: int, voice_client: discord.VoiceClient, channel_id: int, bot: discord.ext.commands.Bot,
                 queue: list[str]):
        self.guild_id = guild_id
        self.voice_client: VoiceClient = voice_client
        self.channel_id = channel_id
        self._queue = queue
        self.current_song = None
        self.bot = bot

    def add_to_queue(self, song: str, ctx: SlashContext):
        self._queue.append(song)
        video = search(song)[1]
        ctx.reply(f"Added {video} to the queue")

    def start_playing(self, force=False):
        if not self.voice_client.is_playing():
            if self.voice_client.is_paused() and not force:
                self.voice_client.resume()
                return True
            self.current_song = self._queue.pop(0)
            url, video_link = start_playing_song(self.current_song, self.voice_client, self.callback)
            self.bot.get_channel(self.channel_id).send(f"Now playing: {video_link}")
            return True
        return False

    def skip_song(self, ctx: SlashContext):
        self.voice_client.stop()
        self.start_playing(force=True)
        ctx.reply("Song skipped")

    def callback(self, error, *args):
        if error:
            self.bot.get_channel(self.channel_id).send(f"Error: {error}")
        else:
            self.start_playing()


class GuildSessionManager:
    def __init__(self, bot):
        self.sessions = {}
        self._bot = bot

    def create_session(self, guild_id, voice_client, channel_id, queue: list[str], overwrite=False):
        if guild_id in self.sessions and not overwrite:
            self.sessions[guild_id].voice_client = voice_client
            self.sessions[guild_id].channel_id = channel_id
            return False
        self.sessions[guild_id] = GuildSession(guild_id, voice_client, channel_id, self._bot, queue)
        return True

    def get_session(self, guild_id) -> GuildSession:
        return self.sessions[guild_id]

    def get_or_create_session(self, guild_id, voice_client, channel_id, queue: list[str]) -> GuildSession:
        if guild_id in self.sessions:
            return self.sessions[guild_id]
        else:
            self.create_session(guild_id, voice_client, channel_id, queue)
            return self.sessions[guild_id]

    def remove_session(self, guild_id):
        del self.sessions[guild_id]
