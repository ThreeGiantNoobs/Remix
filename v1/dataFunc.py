import re
import os
import json

import requests
import youtube_dl
import dotenv

dotenv.load_dotenv()
with open('config.json') as config_file:
    config = json.load(config_file)

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'cachedir': False, 'nocheckcertificate': True}

yt_link_pat = re.compile(r'(?:https?://)?(?:www\.)?youtu(?:be)?\.(?:com|be)(?:/watch/?\?v=|/embed/|/shorts/|/)(\w+)')
spotify_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/track/(\w+)')
spotify_playlist_pattern = re.compile(r'(?:https?://)?(?:www\.)?open\.spotify\.com/playlist/(\w+)')


def search(query):
    query = get_url(query)
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        response = ydl.extract_info(f"ytsearch: {query}", download=False)['entries'][0]
        video_url, video = response['url'], response['webpage_url']
    return video_url, video


def get_title(query):
    match = re.match(spotify_playlist_pattern, query)
    if match:
        return "Playlist"
    query = get_url(query)
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        response = ydl.extract_info(f"ytsearch: {query}", download=False)['entries'][0]
        return response['title']


def get_spotify_title(spotify_track_id):
    spotify_url = f'https://open.spotify.com/track/{spotify_track_id}'
    response = requests.get(spotify_url)
    title = re.search(r'<title>(.*?)</title>', response.text).group(1).replace('| Spotify', '').strip()
    return title


def get_url(url):
    match = re.match(yt_link_pat, url)
    spotify_match = re.match(spotify_pattern, url)
    spotify_playlist_match = re.match(spotify_playlist_pattern, url)
    if match:
        return f'"{match[1]}"'
    elif spotify_match:
        return get_spotify_title(spotify_match[1])
    elif spotify_playlist_match:
        return "dQw4w9WgXcQ"
        # return get_tracks_from_spotify_playlist(spotify_playlist_match[1])
    else:
        return url


def get_tracks_from_spotify_playlist(spotify_playlist_id):
    spotify_token = config["SPOTIFY"]["API_TOKEN"]
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {spotify_token}'
    }
    
    spotify_url = f'https://api.spotify.com/v1/playlists/{spotify_playlist_id}/tracks?offset=0&limit=100'
    response = requests.get(spotify_url, headers=headers)
    
    if response.status_code != 200:
        return False
    else:
        tracks = response.json()['items']
        tracks = [track['track']['name'] + " " + track['artists'][0] for track in tracks]
        return tracks
