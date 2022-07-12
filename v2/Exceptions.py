class AuthorVoiceException(Exception):
    def __init__(self, author):
        self.message = f"{author} is not in any voice channel"


class BotVoiceException(Exception):
    def __init__(self, bot):
        self.message = f"{bot} is not in any voice channel"


class PlayerNotFoundException(Exception):
    def __init__(self, server):
        self.message = f"Player does not exist for {server}"


class AlreadyPlayingException(Exception):
    def __init__(self, bot, channel):
        self.message = f"{bot} is already in <#{channel}>"


class AlreadyConnectedException(Exception):
    def __init__(self, bot, channel):
        self.message = f"{bot} is already connected to {channel}"


class NotConnectedException(Exception):
    def __init__(self, bot, channel=None):
        if not channel:
            self.message = f"{bot} is not connected to any channel"
        else:
            self.message = f"{bot} is not connected to {channel}"
            

class SessionNotFoundException(Exception):
    def __init__(self, channel):
        self.message = f"Session does not exist for {channel}"


class NotPlayingException(Exception):
    def __init__(self, bot):
        self.message = f"{bot} is not playing anything"


class NotPausedException(Exception):
    def __init__(self, bot):
        self.message = f"{bot} is not paused"


class AlreadyStoppedException(Exception):
    def __init__(self, bot):
        self.message = f"{bot} is already stopped"


class SongNotFoundException(Exception):
    def __init__(self, song):
        self.message = f"Song {song} not found. Try using youtube URL instead."


class EmptyQueueError(Exception):
    def __init__(self):
        self.message = "Queue is empty"


class VolumeOutOfBoundsException(Exception):
    def __init__(self, volume):
        self.message = f"Volume {volume} can't be set. It must be between 0 and 100"


class UnsupportedUrlException(Exception):
    def __init__(self, type):
        self.message = f"{type} links are not supported"
