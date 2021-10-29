import asyncio
import threading
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
        return None, None


# def async_callback(fun, *args):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#
#     loop.run_until_complete(fun(*args))
#     loop.close()


def run_async(coroutine, client: discord.ext.commands.Bot):
    future = asyncio.run_coroutine_threadsafe(coroutine, client.loop)
    try:
        print(future.done())
    except Exception as e:
        print(e)
        traceback.print_exc()
    # thread = threading.Thread(target=async_callback, args=[fun, *args])
    # return thread
