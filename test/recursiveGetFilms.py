from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import os
import textwrap
import tempfile
from time import sleep
from serpapi import GoogleSearch
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import TextLoader
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, StuffDocumentsChain
from extractFilms import extract_films_titles_from_text

load_dotenv()

# Function to get top 5 links from a search query
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
        print(f"Error fetching top 5 links for query '{query}': {e}")
        return []

# Function to get page content and chunk it
def get_page_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 ..."}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        clean_text = '\\n'.join(chunk for chunk in chunks if chunk)

        words = clean_text.split()
        chunks = [' '.join(words[i:i + 500]) for i in range(0, len(words), 500)]
        return chunks
    except requests.RequestException as e:
        print(f"Error fetching content for URL '{url}': {e}")
        return []

# Function to summarize text with LangChain
def summarize_with_langchain(chunks, director_name):
    summarized_content = ""
    for chunk in chunks:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(chunk)
            temp_file_path = temp_file.name

        loader = TextLoader(temp_file_path)
        docs = loader.load()

        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
        prompt_template = PromptTemplate(
            template="Summarize the following text focusing on film titles and relevant information about the director {director_name}. "
                     "Exclude any unrelated content. Ensure all film titles in the text are preserved in the summary.",
            input_variables=["director_name"]
        )
        llm_chain = LLMChain(llm=llm, prompt=prompt_template)

        stuff_chain = StuffDocumentsChain(
            llm_chain=llm_chain,
            document_prompt=PromptTemplate(template="{document_content}"),
            document_variable_name="document_content"
        )

        summarized_chunk = stuff_chain.run(input_documents=docs, additional_args={'director_name': director_name}, max_tokens=13000)
        summarized_content += " " + summarized_chunk
        os.unlink(temp_file_path)

    return summarized_content.strip()

# Main function to get influences of directors
def get_influences(director_names):
    for director in director_names:
        links = get_top_5_links(f"{director}'s favorite films")
        all_summaries = []

        for link in links:
            chunks = get_page_content(link)
            summarized_chunks = summarize_with_langchain(chunks, director)
            all_summaries.append(summarized_chunks)
            sleep(2)

        final_summary = ' '.join(all_summaries)
        with open(f"{director}_content_summary.txt", "w", encoding="utf-8") as file:
            file.write(final_summary)

        film_titles = extract_films_titles_from_text(final_summary)
        with open(f"{director}_film_list.txt", "w", encoding="utf-8") as file:
            for film in film_titles:
                file.write(f"{film}\\n")

if __name__ == "__main__":
    director_names = [
        "Steven Spielberg", "Martin Scorsese", "Alfred Hitchcock", "Stanley Kubrick",
        "Quentin Tarantino", "Christopher Nolan", "Ridley Scott", "Francis Ford Coppola",
        "James Cameron", "Ingmar Bergman", "Akira Kurosawa"
    ]
    get_influences(director_names)