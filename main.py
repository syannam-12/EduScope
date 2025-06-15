from flask import Flask, render_template, request, jsonify
import requests
import nltk
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from googlesearch import search
import wikipediaapi
import nltk
nltk.data.path.append("C:\\Users\\srava\\AppData\\Roaming\\nltk_data")



app = Flask(__name__)

nltk.download('punkt_tab')
# Function to summarize text
def summarize_text(text, sentences_count=5):
    if not text.strip():
        return "No meaningful content available for summarization."
    
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join(str(sentence) for sentence in summary)

# Function to extract text from a URL
def extract_text_from_url(url):
    if not url or not url.startswith("http"):
        print("Invalid URL:", url)
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}  # Bypass bot detection
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract meaningful text from paragraphs
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50)

        return text if len(text) > 200 else None  # Ensure it's valid content
    except requests.exceptions.RequestException as e:
        print("Error fetching URL:", e)
        return None

# Function to search Google and fetch multiple links
def search_google(topic, num_results=5):
    try:
        search_results = list(search(topic, num_results=num_results))
        valid_urls = [url for url in search_results if url.startswith("http")]
        return valid_urls[:num_results]  # Return only top valid URLs
    except Exception as e:
        print("Error fetching search results:", e)
        return []

# Function to summarize from multiple sources
def summarize_from_search(topic):
    urls = search_google(topic, num_results=5)
    combined_text = ""

    for url in urls:
        extracted_text = extract_text_from_url(url)
        if extracted_text:
            combined_text += extracted_text + "\n"

    if combined_text:
        return summarize_text(combined_text, sentences_count=5)
    
    return "No valid text found for summarization."

# Function to fetch summary from Wikipedia
def search_wikipedia(topic):
    wiki_wiki = wikipediaapi.Wikipedia("en")
    page = wiki_wiki.page(topic)
    return page.summary if page.exists() else None


@app.route("/summarize-text", methods=["POST"])
def summarize():
    data = request.json
    
    if "url" in data:
        extracted_text = extract_text_from_url(data["url"])
        if extracted_text:
            summary = summarize_text(extracted_text)
            return jsonify({"summary": summary})
        return jsonify({"error": "Could not extract meaningful text from URL."}), 400
    
    elif "topic" in data:
        # wiki_summary = search_wikipedia(data["topic"])
        # if wiki_summary:
        #     return jsonify({"summary": summarize_text(wiki_summary)})
        
        google_summary = summarize_from_search(data["topic"])
        if google_summary:
            return jsonify({"summary": google_summary})
    
    return jsonify({"error": "Invalid input. Provide either 'topic' or 'url'."}), 400

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
