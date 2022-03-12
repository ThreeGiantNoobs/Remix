import re
import os

import lyricsgenius as lg
import requests
import youtube_dl
import dotenv

from spotify_api import get_song_spotify

dotenv.load_dotenv()

GENIUS_API_KEY = os.getenv("GENIUS_TOKEN")
YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'cachedir': False, 'nocheckcertificate': True}

yt_link_pat = re.compile(r'(?:https?://)?(?:www\.)?youtu(?:be)?\.(?:com|be)(?:/watch/?\?v=|/embed/|/shorts/|/)(\w+)')
spotify_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/track/(\w+)')
spotify_playlist_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/playlist/(\w+)')

genius = lg.Genius(GENIUS_API_KEY,
                   skip_non_songs=True,
                   excluded_terms=["(Remix)", "(Live)"],
                   remove_section_headers=True)


def parse_video(yt_video):
    video_url = yt_video.get("url", None)
    webpage_url = yt_video.get("webpage_url", None)
    video_id = yt_video.get("id", None)
    video_title = yt_video.get('title', None)
    artist = yt_video.get('uploader', None)
    thumbnail_url = yt_video.get("thumbnails", None)[-1]["url"]

    return {"video_title": video_title,
            "video_id": video_id,
            "video_dl_url": video_url,
            "video_url": webpage_url,
            "artist": artist,
            "thumbnail_url": thumbnail_url}


def _check_query(query):
    yt_match = re.match(yt_link_pat, query)
    spotify_match = re.match(spotify_pattern, query)
    spotify_playlist_match = re.match(spotify_playlist_pattern, query)
    if yt_match:
        return "yt", yt_match.group(1)
    if spotify_match:
        return "spotify", spotify_match.group(1)
    if spotify_playlist_match:
        return "spotify_playlist", spotify_playlist_match.group(1)

    return "text", query


def get_data(query, run=False):
    q_type, processed_query = _check_query(query)
    if q_type == "yt":
        return {**_get_yt_data(processed_query),
                "query": query,
                "explicit": False}
    elif q_type == "text":
        song = get_song_spotify(processed_query)
        return {**_search_yt(f"{song['name']} \
        {' '.join(song['artists'])} \
        {'lyrics' if run else ''}"),
                "query": query,
                "explicit": song["explicit"]}


def _get_yt_data(video_id):
    base_url = "https://www.youtube.com/watch?v="
    url = base_url + video_id
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info_dict = ydl.extract_info(url, download=False)

    return parse_video(info_dict)


def genius_lyrics(artist, song):
    try:
        song = genius.search_song(song, artist)
        lyrics = song.lyrics
        return lyrics
    except:
        return None


def textyl_lyrics(song, artist=None):
    BASE_URL = "https://api.textyl.co/api/lyrics"
    response = requests.get(f"{BASE_URL}?q={song}{f' {artist}' if artist else ' '}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


def _search_yt(query):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info_dict = ydl.extract_info(f"ytsearch: {query}", download=False)["entries"][0]

    return parse_video(info_dict)


if __name__ == '__main__':
    print(get_data("hello"))
