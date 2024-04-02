from dotenv import load_dotenv

import requests
import csv
from bs4 import BeautifulSoup
import time
import os
from serpapi import GoogleSearch
from extractFilms import extract_films_titles_from_text

load_dotenv()

def get_top_5_links(query):
    """Retrieve top 5 hits from SerpApi's Google search."""
    try:
        params = {
            "q": query,
            "hl": "en",
            "gl": "us",
            "google_domain": "google.com",
            "api_key": os.getenv('SERPAPI_KEY')
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        links = [result['link'] for result in results['organic_results']][:5]
        return links

    except Exception as e:
        print(f"Error at func(get_top_5_links) fetching top 5 links for query '{query}': {e}")
        return []

def get_page_content(url):
    """Retrieve clean text content of a webpage."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status() # check for error

        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): # dump js and css
            script.extract()
        text = soup.get_text()

        # I had a bad experience dealing with
        # webpage content without doing the
        # following cleanup

        # separate lines, remove leading and trailing spaces on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        # drop blank lines
        clean_text = ('\n'.join(chunk for chunk in chunks if chunk))

        return clean_text

    except requests.RequestException as e:
        print(f"Error fetching content for URL '{url}': {e}")
        return ''

def get_influences(director_names):
    """Use the clean content and the extractFilm module to encapsulate films in a dictionary."""

    director_film_mapping = {}
    for director in director_names:
        # Get top 5 hits for query
        links = get_top_5_links(f"{director}'s favorite films")

        # Concatenate content from top 5 links
        # and encapsulate with director
        concatenated_content = ""
        for link in links:
            content = get_page_content(link)
            concatenated_content += content
            time.sleep(2) # Rest

        if concatenated_content:
            # Extract film titles using extractFilms
            try:
                film_titles = extract_films_titles_from_text(concatenated_content)
            except Exception as e:
                print(f"Error extracting film titles for director '{director}': {e}")
                continue

            # Store in dictionary
            director_film_mapping[director] = film_titles

        print(f"Encapsulated films for {director}")

    return director_film_mapping

if __name__ == "__main__":
    director_names = [
        "Steven Spielberg", "Martin Scorsese", "Alfred Hitchcock", "Stanley Kubrick",
        "Quentin Tarantino", "Christopher Nolan", "Ridley Scott", "Francis Ford Coppola",
        "James Cameron", "Ingmar Bergman", "Akira Kurosawa"
    ]
    print(get_influences(director_names))