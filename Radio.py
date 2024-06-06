#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 12:29:01 2024

@author: samhegeman
"""

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import random
import time
import pandas as pd

# Radio location-recommendation 

# Set up Spotify credentials
SPOTIPY_CLIENT_ID = '4490ca098c264328b40fadabb2f365a2'
SPOTIPY_CLIENT_SECRET = '244962c07ad8472fa469587b9bb25f09'
SPOTIPY_REDIRECT_URI = 'http://localhost:8501'

# Set up Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope='user-top-read user-read-recently-played')

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=sp_oauth)

# Function to get user's location using IP geolocation
def get_user_location():
    response = requests.get('https://ipinfo.io')
    location_data = response.json()
    user_location = location_data.get('city')
    user_country = location_data.get('country')
    return user_location, user_country

# Function to get top tracks based on the user's listening history
def get_top_tracks():
    top_tracks_data = sp.current_user_top_tracks(limit=10, time_range='short_term')
    top_tracks = top_tracks_data['items']
    return top_tracks

# Function to get popular tracks from a CSV file
def get_popular_tracks_from_csv(csv_file='/Users/samhegeman/Documents/Bigdata/Pythoncode/data.csv'):
    df = pd.read_csv(csv_file)
    popular_tracks = []
    for _, row in df.iterrows():
        track_info = {
            'name': row['track_name'],
            'artists': [{'name': row['artist_names']}],
            'preview_url': None  # Assuming we don't have preview URLs in the CSV
        }
        popular_tracks.append(track_info)
    return popular_tracks

# Function to combine top tracks with popular tracks
def combine_tracks(user_tracks, popular_tracks, user_ratio=0.5):
    combined_tracks = []
    num_user_tracks = int(len(user_tracks) * user_ratio)
    num_popular_tracks = len(user_tracks) - num_user_tracks
    
    combined_tracks.extend(random.sample(user_tracks, num_user_tracks))
    combined_tracks.extend(random.sample(popular_tracks, num_popular_tracks))
    
    random.shuffle(combined_tracks)
    return combined_tracks

# Main Streamlit app
def main():
    st.title('Location-Based Spotify Radio')
    
    user_location, user_country = get_user_location()
    st.write(f'User Location: {user_location}, {user_country}')
    
    if user_location:
        st.write('Creating a radio station with a mix of your top tracks and popular songs in your area...')
        
        # Allow user to set the ratio of personal vs. popular tracks
        user_ratio = st.slider('Ratio of personal to popular tracks', 0.0, 1.0, 0.5)
        
        # Continuously update the radio station
        while True:
            user_top_tracks = get_top_tracks()
            popular_tracks = get_popular_tracks_from_csv()
            
            combined_tracks = combine_tracks(user_top_tracks, popular_tracks, user_ratio)
            
            if combined_tracks:
                st.write('Now playing the combined top tracks and popular tracks in your area:')
                for track in combined_tracks:
                    st.write(f"{track['name']} by {track['artists'][0]['name']}")
                    # Add track preview if available
                    if track['preview_url']:
                        st.audio(track['preview_url'], format="audio/mp3")
            
            # Update every 10 minutes, to update the radio continuously
            time.sleep(600)
            st.experimental_rerun()

if __name__ == '__main__':
    main()
