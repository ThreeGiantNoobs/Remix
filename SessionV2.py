from typing import Optional

from Exceptions import *
from dataFuncV2 import *


class Song:
    def __init__(self, title: str, vid_id: str, dl_url: str, video_url: str):
        self.title = title
        self.id = vid_id
        self.dl_url = dl_url
        self.video_url = video_url


class Session:
    def __init__(self, player):
        self.player = player
        self.queue: list[Song] = []
        self.current_song: Optional[Song] = None
        self.previous_song: Optional[Song] = None
    
    def add_song(self, query: str):
        song = get_data(query)
        song = Song(song['video_title'], song['video_id'], song['video_dl_url'], song['video_url'])
        self.queue.append(song)
        return song
        
    def play_song(self, query: str):
        if not self.queue:
            ...
    

class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def _create_session(self, player):
        session = Session(player)
        self.sessions[player] = session
        return session
    
    def _get_session(self, player):
        session = self.sessions.get(player)
        if not session:
            raise SessionNotFoundException(player.guild.name)
    
    def get_or_create_session(self, player) -> Session:
        try:
            return self._get_session(player)
        except SessionNotFoundException:
            return self._create_session(player)
    
    def delete_session(self, player):
        if player in self.sessions:
            del self.sessions[player]
            return True
        raise SessionNotFoundException(player.guild.name)
    
    def get_all_sessions(self):
        return self.sessions.values()
