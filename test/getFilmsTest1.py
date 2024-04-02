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
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

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
        links = [result['link'] for result in results['organic_results']][:5]
        return links

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

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        clean_text = ('\n'.join(chunk for chunk in chunks if chunk))

        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(clean_text)
        return texts

    except requests.RequestException as e:
        print(f"Error fetching content for URL '{url}': {e}")
        return ''

prompt_template = PromptTemplate.from_template(
    "Summarize the following text focusing on film titles and relevant information about the director {director_name}. "
    "Exclude any unrelated content such as advertisements, subscription requests, or non-film-related details. "
    "Ensure that all film titles mentioned in the text are preserved in the summary."
)

def summarize_with_langchain(text_chunks, director_name):
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    chain = load_summarize_chain(llm, chain_type='map_reduce')

    # The original prompt template logic
    prompt_template = PromptTemplate.from_template(
        "Summarize the following text focusing on film titles and relevant information about the director {director_name}. "
        "Exclude any unrelated content such as advertisements, subscription requests, or non-film-related details. "
        "Ensure that all film titles mentioned in the text are preserved in the summary."
    )

    summarized_content = ''
    for chunk in text_chunks:
        # Process the chunk directly without writing to a file
        docs = [chunk]

        # Use the summarization chain with your custom prompt
        for doc in docs:
            response = chain.run(docs, additional_args={'director_name': director_name}, max_tokens=13000)
            summarized_content += response + ' '  # Concatenate responses

    return summarized_content

def get_influences(director_names):
    for director in director_names:
        links = get_top_5_links(f"{director}'s favorite films")

        for i, link in enumerate(links, start=1):
            text_chunks = get_page_content(link)
            summarized_contents = []

            for chunk in text_chunks:
                summarized_chunk = summarize_with_langchain([chunk], director)
                summarized_contents.append(summarized_chunk)

            combined_summary = ' '.join(summarized_contents)

            summary_file_path = f"{director}_content_{i}.txt"
            with open(summary_file_path, "w", encoding="utf-8") as file:
                file.write(combined_summary)

            time.sleep(2)

        final_content = ""
        for i in range(1, 6):
            with open(f"{director}_content_{i}.txt", "r", encoding="utf-8") as file:
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