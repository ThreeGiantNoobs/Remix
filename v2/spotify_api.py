from typing import TypedDict, List

import os
import base64
import requests
import json
import time

import dotenv
from Exceptions import SongNotFoundException

dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

with open('config.json') as config:
    config = json.load(config)
spotify_config = config['SPOTIFY_CREDS']

client_id = spotify_config["CLIENT_ID"]
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
token_url = spotify_config["TOKEN_URL"]
api_token = os.getenv("SPOTIFY_API_TOKEN")
expire_time = spotify_config["TOKEN_EXPIRE_TIME"]


class Spotify_Song(TypedDict):
    name: str
    artists: List[str]
    explicit: bool


def _get_api_token():
    global client_id, client_secret, token_url, api_token, expire_time
    if time.time() < expire_time:
        return api_token
    
    id_secret = f'{client_id}:{client_secret}'
    encoded_id_secret = base64.b64encode(id_secret.encode('utf-8')).decode()
    
    payload = {'grant_type': 'client_credentials'}
    headers = {
        'Authorization': 'Basic ' + encoded_id_secret,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, data=payload, headers=headers)
    response_json = response.json()

    api_token = response_json['access_token']
    expire_time = time.time() + response_json['expires_in']

    os.environ["SPOTIFY_API_TOKEN"] = api_token
    dotenv.set_key(dotenv_file, 'SPOTIFY_API_TOKEN', os.environ["SPOTIFY_API_TOKEN"])
    spotify_config['TOKEN_EXPIRE_TIME'] = expire_time
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)
        
    return api_token


def get_song_spotify(q_type, query):
    song = None

    api_token = _get_api_token()
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    if q_type == "text":
        args = {
            'q': query,
            'type': 'track',
            'limit': 1
        }

        response = requests.get(f'https://api.spotify.com/v1/search?', params=args, headers=headers)
        response_json = response.json()

        song = response_json['tracks']['items']
        if len(song) == 0:
            raise SongNotFoundException(query)
        song = song[0]

        song = Spotify_Song(
            name=song['name'],
            artists=[artist['name'] for artist in song['artists']],
            explicit=song['explicit']
        )

    elif q_type == "spotify":
        song_id = query

        response = requests.get(f'https://api.spotify.com/v1/tracks/{song_id}', headers=headers)

        try:
            song = response.json()
        except json.decoder.JSONDecodeError:
            raise SongNotFoundException(query)

        song = Spotify_Song(
            name=song['name'],
            artists=[artist['name'] for artist in song['artists']],
            explicit=song['explicit']
        )

    return song


if __name__ == '__main__':
    # song = get_song_spotify("text", "Bang Bang Adam Levine")
    song = get_song_spotify("spotify", "55p8TQ1ggGYOO1gLQrC52D?si=ec9f6dbc371944d8")
    print(song)
