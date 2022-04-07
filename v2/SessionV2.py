from typing import Optional
from enum import Enum

from Exceptions import *
from dataFuncV2 import *


class Actions(Enum):
    ERROR = 0
    PLAY = 1
    QUEUE = 2


class Song:
    def __init__(self, query: str,
                 title: str,
                 vid_id: str,
                 dl_url: str,
                 video_url: str,
                 thumbnail: str,
                 artist: str,
                 explicit: bool):
        self.query = query
        self.title = title
        self.id = vid_id
        self.dl_url = dl_url
        self.video_url = video_url
        self.thumbnail = thumbnail
        self.artist = artist
        self.explicit = explicit


class Session:
    class Queue(list):
        def check_zero(self):
            if len(self) == 0:
                self.session.player.stop_player()
                self.session.previous_song = self.session.current_song
                self.session.current_song = None
            elif self[0] != self.session.current_song:
                if self.session.player.status() != 3:
                    self.session.player.stop_player()
                    self.session.player.run_song(self[0])
                    self.session.previous_song = self.session.current_song
                    self.session.current_song = self[0]

        def __setitem__(self, key, value):
            super(Session.Queue, self).__setitem__(key, value)
            self.check_zero()

        def __delitem__(self, key):
            super(Session.Queue, self).__delitem__(key)
            self.check_zero()

        def append(self, value):
            super(Session.Queue, self).append(value)
            self.check_zero()

        def insert(self, index, value):
            super(Session.Queue, self).insert(index, value)
            self.check_zero()

        def pop(self, index=-1):
            super(Session.Queue, self).pop(index)
            self.check_zero()

        def __init__(self, session, queue=None):
            if queue is None:
                queue = []
            super(Session.Queue, self).__init__(queue)
            self.session = session

    def __init__(self, player):
        self.player = player
        self.queue: Session.Queue[Song] = Session.Queue(self)
        self.current_song: Optional[Song] = None
        self.previous_song: Optional[Song] = None

    def _get_song(self, query: str):
        song = get_data(query)
        song = Song(query=song['query'],
                    title=song['video_title'],
                    vid_id=song['video_id'],
                    dl_url=song['video_dl_url'],
                    video_url=song['video_url'],
                    thumbnail=song['thumbnail_url'],
                    artist=song['artist'],
                    explicit=song['explicit'])

        return song

    def queue_song(self, query: str):
        song = self._get_song(query)
        self.queue.append(song)
        return song

    def remove_latest(self):
        return self.queue.pop(0)


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
        return session

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

    def reset_session(self, player):
        try:
            self.delete_session(player)
        except SessionNotFoundException:
            raise SessionNotFoundException
        return self.get_or_create_session(player)

    def get_all_sessions(self):
        return self.sessions.values()
