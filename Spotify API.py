import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")


def auth_spotify():
    token_url = 'https://accounts.spotify.com/api/token'
    id_secret = f'{client_id}:{client_secret}'
    
    encoded_id_secret = base64.b64encode(id_secret.encode('utf-8')).decode()
    
    payload = {'grant_type': 'client_credentials'}
    headers = {
        'Authorization': 'Basic ' + encoded_id_secret,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, data=payload, headers=headers)
    
    return response.json()


if __name__ == '__main__':
    print(auth_spotify())
