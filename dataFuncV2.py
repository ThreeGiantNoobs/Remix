import re
import os

import requests
import youtube_dl
import dotenv

dotenv.load_dotenv()

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'cachedir': False, 'nocheckcertificate': True}

yt_link_pat = re.compile(r'(?:https?://)?(?:www\.)?youtu(?:be)?\.(?:com|be)(?:/watch/?\?v=|/embed/|/shorts/|/)(\w+)')
spotify_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/track/(\w+)')
spotify_playlist_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/playlist/(\w+)')


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
    

def get_data(query):
    q_type, query = _check_query(query)
    if q_type == "yt":
        return _get_yt_data(query)
    
    
def _get_yt_data(video_id):
    base_url = "https://www.youtube.com/watch?v="
    url = base_url + video_id
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_url = info_dict.get("url", None)
        video_id = info_dict.get("id", None)
        video_title = info_dict.get('title', None)
    
    return {"video_title": video_title, "video_id": video_id, "video_dl_url": video_url, "video_url": url}
