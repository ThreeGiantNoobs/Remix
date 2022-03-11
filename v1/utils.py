import asyncio
import traceback

from discord import VoiceClient, FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext.commands import Bot

from dataFunc import search


def start_playing_song(query: str, voice_client: VoiceClient, callback) -> (str, str):
    try:
        url, video_link = search(query)

        voice_client.play(FFmpegPCMAudio(url), after=callback)
        voice_client.source = PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = 0.5
        return url, video_link
    except Exception as e:
        print(e)
        traceback.print_exc()


# def async_callback(fun, *args):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#
#     loop.run_until_complete(fun(*args))
#     loop.close()


def run_async(coroutine, client: Bot):
    future = asyncio.run_coroutine_threadsafe(coroutine, client.loop)
    try:
        print(future.done())
    except Exception as e:
        print(e)
        traceback.print_exc()
    # thread = threading.Thread(target=async_callback, args=[fun, *args])
    # return thread
