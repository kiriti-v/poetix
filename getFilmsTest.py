from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time
import os
from serpapi import GoogleSearch
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import TextLoader
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, StuffDocumentsChain
from extractFilms import extract_films_titles_from_text

load_dotenv()

def get_top_5_links(query):
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
        if 'organic_results' in results:
            links = [result['link'] for result in results['organic_results']][:5]
            return links
        else:
            print(f"No organic results found for query '{query}'")
            return []

    except Exception as e:
        print(f"Error at func(get_top_5_links) fetching top 5 links for query '{query}': {e}")
        return []

def get_page_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 ..."
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()

        # Split the text into lines, then into words, stripping whitespace
        lines = (line.strip() for line in text.splitlines())
        words = (word for line in lines for word in line.split())

        # Take words up to the word limit
        word_limit = 2100
        limited_words = []
        for word in words:
            if len(limited_words) < word_limit:
                limited_words.append(word)
            else:
                break

        # Join the words back into text
        clean_text = ' '.join(limited_words)

        return clean_text

    except requests.RequestException as e:
        print(f"Error fetching content for URL '{url}': {e}")
        return ''

prompt_template = PromptTemplate.from_template(
    "Summarize the following text focusing on film titles and relevant information about the director {director_name}. "
    "Exclude any unrelated content such as advertisements, subscription requests, or non-film-related details. "
    "Ensure that all film titles mentioned in the text are preserved in the summary."
)

def summarize_with_langchain(file_path, director_name):
    loader = TextLoader(file_path)
    docs = loader.load()

    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)

    stuff_chain = StuffDocumentsChain(
        llm_chain=llm_chain,
        document_prompt=PromptTemplate.from_template("{page_content}"),
        document_variable_name="director_name"
    )

    summarized_content = stuff_chain.run(input_documents=docs, additional_args={'director_name': director_name}, max_tokens=13000)
    return summarized_content

def get_influences(director_names):
    for director in director_names:
        links = get_top_5_links(f"{director}'s favorite films")

        if not links:  # Check if links are empty
            print(f"No links found for {director}")
            continue

        for i, link in enumerate(links, start=1):
            content = get_page_content(link)
            temp_file_path = f"temp_{director}_content_{i}.txt"
            summary_file_path = f"{director}_content_{i}.txt"

            with open(temp_file_path, "w", encoding="utf-8") as file:
                file.write(content)

            summarized_content = summarize_with_langchain(temp_file_path, director)

            with open(summary_file_path, "w", encoding="utf-8") as file:
                file.write(summarized_content)

            time.sleep(2)

        final_content = ""
        for i in range(1, 6):
            summary_file = f"{director}_content_{i}.txt"
            if os.path.exists(summary_file):  # Check if the file exists before opening
                with open(summary_file, "r", encoding="utf-8") as file:
                    final_content += file.read() + "\n"

        with open(f"{director}_content_full.txt", "w", encoding="utf-8") as file:
            file.write(final_content)

        film_titles = extract_films_titles_from_text(final_content)
        with open(f"{director}_film_list.txt", "w", encoding="utf-8") as file:
            for film in film_titles:
                file.write(f"{film}\n")

if __name__ == "__main__":
    director_names = [
        "Steven Spielberg", "Martin Scorsese", "Alfred Hitchcock", "Stanley Kubrick",
        "Quentin Tarantino", "Christopher Nolan", "Ridley Scott", "Francis Ford Coppola",
        "James Cameron", "Ingmar Bergman", "Akira Kurosawa"
    ]
    get_influences(director_names)