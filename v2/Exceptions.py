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
