import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

# ... (rest of the code remains the same)
load_dotenv()

client_id= os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token 

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"q={artist_name}&type=artist&limit=1"
    
    query_url = url + "?" + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) == 0:
        print(f"No artist with the name '{artist_name}' exists...")
        return None
    
    return json_result[0]

def get_songs_by_artist(token, artist_id):
    url= f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    return json_result

def get_albums_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["items"]
    return json_result

def get_top_albums_by_artist(token, artist_id, num_albums=2):
    albums = get_albums_by_artist(token, artist_id)

    # Buat kamus untuk mengelompokkan lagu berdasarkan album
    albums_dict = {}
    for album in albums:
        album_name = album["name"]
        albums_dict[album_name] = []

    # Ambil lagu-lagu teratas untuk setiap album
    songs = get_songs_by_artist(token, artist_id)
    for song in songs:
        album_name = song["album"]["name"]
        if album_name in albums_dict:
            albums_dict[album_name].append(song["name"])

    # Pilih 2 album teratas berdasarkan jumlah lagu
    sorted_albums = sorted(albums_dict.items(), key=lambda x: len(x[1]), reverse=True)[:num_albums]

    return sorted_albums

token = get_token()

# Define a function to create a pandas DataFrame for the top songs of an artist
def create_table_for_artist(artist_name, songs):
    data = {
        "Artist": [artist_name] * len(songs),
        "Song Name": [song["name"] for song in songs]
    }
    df = pd.DataFrame(data)
    return df

# Create a connection to the PostgreSQL database
def create_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="151515"
    )

# Function to insert data into the PostgreSQL table
def insert_data_to_table(df, connection):
    try:
        cursor = connection.cursor()
        for _, row in df.iterrows():
            cursor.execute("INSERT INTO top_songs (artist_name, song_name) VALUES (%s, %s)", (row["Artist"], row["Song Name"]))
        connection.commit()
        print("Data inserted successfully!")
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: ", error)

# ... (rest of the code remains the same)

# Cari informasi artis Fourtwnty
artist_name_1 = "Fourtwnty"
result_1 = search_for_artist(token, artist_name_1)
if result_1:
    artist_id_1 = result_1["id"]
    songs_1 = get_songs_by_artist(token, artist_id_1)
    
    # Create a DataFrame for the top songs of the artist
    df_1 = create_table_for_artist(artist_name_1, songs_1)
    print("\nTable Output for Fourtwnty:")
    print(df_1)

    # Connect to the PostgreSQL database
    connection = create_connection()

    # Insert data into the PostgreSQL table
    insert_data_to_table(df_1, connection)

    # Close the connection
    connection.close()

# ... (rest of the code remains the same)
