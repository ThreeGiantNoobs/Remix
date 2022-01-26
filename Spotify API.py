import base64
import requests
import json
import time

with open('config.json') as config:
    config = json.load(config)
spotify_config = config['SPOTIFY_CREDS']

client_id = spotify_config["CLIENT_ID"]
client_secret = spotify_config["CLIENT_SECRET"]
token_url = spotify_config["TOKEN_URL"]
api_token = spotify_config["API_TOKEN"]
expire_time = spotify_config["TOKEN_EXPIRE_TIME"]


def get_api_token():
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
    
    spotify_config['API_TOKEN'] = api_token
    spotify_config['TOKEN_EXPIRE_TIME'] = expire_time
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)
        
    return api_token
