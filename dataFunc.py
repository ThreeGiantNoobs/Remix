import re

import youtube_dl
import requests

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True}
yt_link_pat = re.compile(r'(?:https?://)?(?:www\.)?youtu(?:be)?\.(?:com|be)(?:/watch/?\?v=|/embed/|/shorts/|/)(\w+)')
spotify_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/track/(\w+)')


def search(query):
    query = get_url(query)
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        response = ydl.extract_info(f"ytsearch: {query}", download=False)['entries'][0]
        video_url, video = response['url'], response['webpage_url']
    return video_url, video


def get_spotify_title(spotify_track_id):
    spotify_url = f'https://open.spotify.com/track/{spotify_track_id}'
    response = requests.get(spotify_url)
    title = re.search(r'<title>(.*?)</title>', response.text).group(1).replace('| Spotify', '').strip()
    return title


def get_url(url):
    match = re.match(yt_link_pat, url)
    spotify_match = re.match(spotify_pattern, url)
    if match:
        return match[1]
    elif spotify_match:
        return get_spotify_title(spotify_match[1])
    else:
        return url
