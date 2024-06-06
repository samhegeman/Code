import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from streamlit.components.v1 import html

# Spotify API credentials
SPOTIPY_CLIENT_ID = '4490ca098c264328b40fadabb2f365a2'
SPOTIPY_CLIENT_SECRET = '244962c07ad8472fa469587b9bb25f09'
SPOTIPY_REDIRECT_URI = 'http://localhost:8501'

# Set up Spotify authentication scope
SPOTIFY_SCOPE = 'playlist-modify-public playlist-modify-private'

# Initialize Spotipy with OAuth authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=SPOTIFY_SCOPE))

# Function to create a playlist
def create_playlist(city, track_ids):
    user_id = sp.current_user()['id']
    playlist_name = f"Top Songs in {city}"
    playlist = sp.user_playlist_create(user_id, playlist_name)
    sp.user_playlist_add_tracks(user_id, playlist['id'], track_ids)
    return playlist['external_urls']['spotify']

# Load your dataset
top_songs_by_city = pd.read_csv('/Users/samhegeman/Documents/Bigdata/Pythoncode/data.csv')

# Calculate play count for each track
top_songs_by_city['play_count'] = top_songs_by_city.groupby('track_uri')['track_uri'].transform('count')

# Create a base map
m = folium.Map(location=[20, 0], zoom_start=2)

# Prepare heatmap data and add popups for each city
heat_data = []
for city, data in top_songs_by_city.groupby('city'):
    lat = data['latitude'].values[0]
    lon = data['longitude'].values[0]
    
    # Verify coordinates
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        print(f"Invalid coordinates for city {city}: ({lat}, {lon})")
        continue
    
    popularity = data['play_count'].mean()
    heat_data.append([lat, lon, popularity])
    
    # Create the popup text with the top 10 songs
    popup_text = f"<b>{city}</b><br>"
    track_ids = []
    for i, row in data.iterrows():
        popup_text += f"{i+1}. {row['track_name']} - {row['artist_names']}<br>"
        track_ids.append(row['track_uri'])
    
    # Add a button to create a playlist
    popup_text += f'<br><a href="/?city={city}" target="_blank">Create Playlist</a>'
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

# Add heatmap layer
HeatMap(heat_data).add_to(m)

# Streamlit Layout
st.title("Explore What's Popular Around the World")
st.markdown("Use the map below to explore the top songs in different cities. Click on a city marker to see the songs and create a Spotify playlist.")

# Render the map
html(m.get_root().render(), width=1000, height=600)

# Sidebar for playlist creation
st.sidebar.title("Create Spotify Playlist")
selected_city = st.sidebar.selectbox("Select a City", top_songs_by_city['city'].unique())

if st.sidebar.button("Create Playlist for Selected City"):
    city_tracks = top_songs_by_city[top_songs_by_city['city'] == selected_city]['track_uri'].tolist()
    if city_tracks:
        playlist_url = create_playlist(selected_city, city_tracks)
        st.sidebar.success(f"Playlist created successfully! [Listen on Spotify]({playlist_url})")
    else:
        st.sidebar.error("No tracks found for this city.")

# Check if the user has clicked to create a playlist from the map popup
query_params = st.experimental_get_query_params()
if 'city' in query_params:
    city = query_params['city'][0]
    city_tracks = top_songs_by_city[top_songs_by_city['city'] == city]['track_uri'].tolist()
    if city_tracks:
        playlist_url = create_playlist(city, city_tracks)
        st.success(f"Playlist created successfully! [Listen on Spotify]({playlist_url})")
    else:
        st.error("No tracks found for this city.")
