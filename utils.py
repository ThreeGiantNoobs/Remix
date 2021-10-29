import traceback

import discord

from dataFunc import search


def start_playing_song(query: str, voice_client: discord.VoiceClient, callback) -> (str, str):
    try:
        url, video_link = search(query)

        voice_client.play(discord.FFmpegPCMAudio(url), after=callback)
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = 0.5
        return url, video_link
    except Exception as e:
        print(e)
        traceback.print_exc()
