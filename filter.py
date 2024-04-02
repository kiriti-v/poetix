from dotenv import load_dotenv
import os
import requests
import pandas as pd

# Load environment variables
load_dotenv()
api_key = os.getenv('TMDB_API_KEY')

def get_movie_director(movie_title):
    try:
        # Search for the movie
        search_url = f'https://api.themoviedb.org/3/search/movie?query={movie_title}&api_key={api_key}'
        print(f"Searching for movie: {movie_title}")
        response = requests.get(search_url)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                movie_id = results[0]['id']
                print(f"Found movie ID for '{movie_title}': {movie_id}")

                # Fetch the credits of the movie
                credits_url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}'
                credits_response = requests.get(credits_url)
                if credits_response.status_code == 200:
                    credits = credits_response.json()
                    for crew_member in credits.get('crew', []):
                        if crew_member.get('job') == 'Director':
                            director_name = crew_member.get('name')
                            print(f"Director of '{movie_title}': {director_name}")
                            return director_name
                else:
                    print(f"Failed to get credits for movie ID {movie_id}")
            else:
                print(f"No results found for movie: {movie_title}")
        else:
            print(f"Failed to search for movie: {movie_title}")
        return None
    except requests.RequestException as e:
        print(f"RequestException in get_movie_director: {e}")
        return None

def filter_csv(input_csv_path, output_csv_path):
    df = pd.read_csv(input_csv_path)
    filtered_df = pd.DataFrame(columns=df.columns)

    for index, row in df.iterrows():
        director = get_movie_director(row['Film'])
        if director and director.lower() != row['Director'].lower():
            filtered_df.loc[len(filtered_df)] = row

    filtered_df.to_csv(output_csv_path, index=False)

input_csv_path = 'directors_film_list.csv'
output_csv_path = 'filtered_directors_film_list.csv'
filter_csv(input_csv_path, output_csv_path)