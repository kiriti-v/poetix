from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain
from langchain.document_loaders import TextLoader

load_dotenv()

# Schema
schema = {
    "properties": {
        "film": {"type": "string"},
        "filmmaker": {"type": "string"}
    },
    "required": ["film", "filmmaker"]
}

def extract_films_titles_from_text(text_content):
    """
    Extracts film titles from the given text content.

    Args:
    - text_content (str): The content from which film titles are to be extracted.

    Returns:
    - list: A list of extracted film titles.
    """
    # load_dotenv()

    doc = text_content

    # Run chain
    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    chain = create_extraction_chain(schema, llm)

    return chain.run(doc)

if __name__ == "__main__":
    filepath = 'data/webpages.txt'
    loader = TextLoader(filepath)
    doc = loader.load()
    results = extract_films_titles_from_text(doc)
    print(results)