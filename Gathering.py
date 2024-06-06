#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 21:23:01 2024

@author: samhegeman
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import time
import csv
import pandas as pd
from collections import defaultdict

def get_geolocation():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        loc = data.get("loc")
        lat, lon = loc.split(",")
        post = data.get("postal")
        city = data.get("city")
        country = data.get("country")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return post, city, country, lat, lon, timestamp
    except Exception as e:
        print("Geolocation couldn't be retrieved, an error occurred:", e)
        return None, None, None, None, None, None

def get_genres(artist_uris, album_uri):
    artist_genres = []
    for uri in artist_uris:
        genres = sp.artist(uri)['genres']
        artist_genres.extend(genres)
    album_genres = sp.album(album_uri)['genres']
    return album_genres if album_genres else artist_genres

CLIENT_ID = '4490ca098c264328b40fadabb2f365a2'
CLIENT_SECRET = '244962c07ad8472fa469587b9bb25f09'
REDIRECT_URI = 'http://localhost:8501'
scope = "user-read-playback-state"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, 
                                               client_secret=CLIENT_SECRET, 
                                               redirect_uri=REDIRECT_URI, 
                                               scope=scope))

user_id = sp.current_user()['id']
track_uri = None

header = ['user_id', 'track_name', 'artist_names', 'track_uri', 'album_uri', 'artist_uris', 'genres', 'preview_url', 'postal', 'city', 'country', 'latitude', 'longitude', 'timestamp', 'play_count']

# Read existing data
try:
    data_df = pd.read_csv('data.csv')
except FileNotFoundError:
    data_df = pd.DataFrame(columns=header)

play_count_dict = defaultdict(int)

# Populate play_count_dict from existing data
for uri in data_df['track_uri']:
    play_count_dict[uri] += 1

# Ensure the CSV file has the correct header if it doesn't already exist
if data_df.empty:
    with open('data.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

while True:
    current_playback = sp.current_playback()
    if current_playback is None or not current_playback['is_playing']:
        print("No song is currently playing. Checking again in 10 seconds.")
        time.sleep(10)
        continue

    new_track = current_playback['item']
    new_track_uri = new_track['uri']
    
    if new_track_uri == track_uri:
        print("The same song as 10 seconds ago is still being played. No new data gathered.")
        time.sleep(10)
    else:
        location = get_geolocation()
        if None in location:
            print("Incomplete location data. Skipping entry.")
            time.sleep(10)
            continue

        track_name = new_track['name']
        artists = [artist['name'] for artist in new_track['artists']]
        artist_uris = [artist['uri'] for artist in new_track['artists']]
        album_uri = new_track['album']['uri']
        track_uri = new_track['uri']
        genres = get_genres(artist_uris, album_uri)
        preview_url = new_track['preview_url']
        
        play_count_dict[track_uri] += 1
        play_count = play_count_dict[track_uri]

        with open('data.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            row = [user_id, track_name, ', '.join(artists), track_uri, album_uri, '|'.join(artist_uris), '|'.join(genres), preview_url, *location, play_count]
            writer.writerow(row)
        
        print(f"New song data written: {track_name} by {artists}")
        time.sleep(10)
