import datetime
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from googlesearch import search
import wikipediaapi
import nltk
import os
import subprocess
import speech_recognition as sr
from yt_dlp import YoutubeDL
from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import nltk
nltk.data.path.append("C:\\Users\\srava\\AppData\\Roaming\\nltk_data")


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong secret key


# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
client = MongoClient("mongodb://localhost:27017/")

# Create DB if it doesn't exist (Mongo will create on first insert)
db_name = 'summarizer_db'
db_list = client.list_database_names()

if db_name not in db_list:
    print(f"Database '{db_name}' does not exist. It will be created automatically on first insert.")

db = client[db_name]

# Check collection
if 'users' not in db.list_collection_names():
    print("Creating 'users' collection...")
    db.create_collection('users')  # Optional (Mongo creates it when first doc is inserted anyway)

users_col = db['users']

# Password hasher
bcrypt = Bcrypt(app)

@app.route('/')
def home():
    if 'user' in session:
        return render_template('index.html', user=session['user'])
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if users_col.find_one({'email': email}):
            flash("Email already registered", "danger")
            return redirect('/register')

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        users_col.insert_one({'email': email, 'password': hashed_pw})
        flash("Registration successful! Please login.", "success")
        return redirect('/login')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users_col.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = email
            flash("Login successful!", "success")
            return redirect('/')
        else:
            flash("Invalid credentials", "danger")
            return redirect('/login')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully!", "info")
    return redirect('/login')
# ---------------- TEXT SUMMARIZATION FUNCTIONS ----------------

def save_history(email, query_type, query_text, summary_text):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    history_entry = {
        "timestamp": timestamp,
        "type": query_type,
        "query": query_text,
        "summary": summary_text
    }

    users_col.update_one(
        {"email": email},
        {"$push": {"history": history_entry}}
    )

def summarize_text(text, sentences_count=15):
    if not text.strip():
        return "No meaningful content available for summarization."
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join(str(sentence) for sentence in summary)

def extract_text_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50)
        return text if len(text) > 200 else None
    except Exception as e:
        print("Error fetching URL:", e)
        return None

def search_google(topic, num_results=5):
    try:
        return [url for url in search(topic, num_results=num_results) if url.startswith("http")]
    except Exception as e:
        print("Google Search Error:", e)
        return []

def summarize_from_search(topic):
    urls = search_google(topic)
    combined_text = ""
    for url in urls:
        content = extract_text_from_url(url)
        if content:
            combined_text += content + "\n"
    return summarize_text(combined_text) if combined_text else "No valid content found."

def search_wikipedia(topic):
    wiki = wikipediaapi.Wikipedia("en")
    page = wiki.page(topic)
    return page.summary if page.exists() else None

# ---------------- VIDEO SUMMARIZATION FUNCTIONS ----------------

def search_youtube_video(query, max_duration=180):
    try:
        options = {
            'quiet': True,
            'format': 'bestaudio/best',
            'extract_flat': 'in_playlist',
            'default_search': 'ytsearch10',
            'force_generic_extractor': False,
        }
        with YoutubeDL(options) as ydl:
            search_result = ydl.extract_info(f"ytsearch1:{query}", download=True)
            print(search_result)
            for entry in search_result['entries']:
                if entry.get('duration') and entry['duration'] <= max_duration:
                    return entry['url']  # return direct video URL
        return None
    except Exception as e:
        print("YouTube Search Error:", e)
        return None

def download_youtube_video(url):
    try:
        options = {
            'format': 'bestaudio/best',
            'outtmpl': 'video_audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        return "video_audio.wav"
    except Exception as e:
        print("Download Error:", e)
        return None

def extract_audio(video_path):
    try:
        audio_path = "video_audio.wav"
        subprocess.run([
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            audio_path, "-y"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return audio_path if os.path.exists(audio_path) else None
    except Exception as e:
        print("Audio extraction error:", str(e))
        return None

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Google Speech API error: {e}"

def simple_summarizer(text, max_sentences=3):
    sentences = text.split('.')
    return '. '.join(sentences[:max_sentences]).strip() + '.'

# ---------------- ROUTES ----------------



@app.route("/summarize-text", methods=["POST"])
def handle_text_summary():
    data = request.get_json()

    if "url" in data:
        content = extract_text_from_url(data["url"])
        if content:
            summary = summarize_text(content)
            # Save history
            if 'user' in session:
                save_history(session['user'], "text_summarization_url", data["url"], summary)
            return jsonify({"summary": summary})
        return jsonify({"error": "Could not extract text."}), 400

    elif "topic" in data:
        summary = summarize_from_search(data["topic"])
        # Save history
        if 'user' in session:
            save_history(session['user'], "text_summarization_topic", data["topic"], summary)
        return jsonify({"summary": summary})

    return jsonify({"error": "Please provide 'url' or 'topic'"}), 400

@app.route("/vindex")
def video_home():
    return render_template("vindex.html")

@app.route("/summarize-video-url", methods=["POST"])
def summarize_video_from_url():
    video_input = request.form.get("url")
    if not video_input:
        return jsonify({"error": "No video input provided."}), 400

    video_url = video_input if "youtube.com" in video_input or "youtu.be" in video_input else search_youtube_video(video_input)
    if not video_url:
        return jsonify({"error": "No valid YouTube video found."}), 404

    audio_path = download_youtube_video(video_url)
    if not audio_path:
        return jsonify({"error": "Audio download failed."}), 500

    transcript = transcribe_audio(audio_path)
    summary = simple_summarizer(transcript)

    # Save user history
    if 'user' in session:
        save_history(session['user'], "video_summarization_url", video_input, summary)

    if os.path.exists(audio_path):
        os.remove(audio_path)

    return jsonify({
        "searched_text": video_input,
        "video_url": video_url,
        "summary": summary
    })

@app.route("/history")
def history():
    if 'user' in session:
        
        print(session['user'])
        user = users_col.find_one({"email": session['user']})
        print(user)
        user_history = user.get('history', [])
        return render_template("history.html", history=user_history, user=user['email'])
    else:
        return redirect("/login")

@app.route("/summarize-video", methods=["POST"])
def summarize_uploaded_video():
    if "file" not in request.files:
        return jsonify({"error": "No video file uploaded."}), 400

    file = request.files["file"]
    file.save("uploaded_video.mp4")

    audio_path = extract_audio("uploaded_video.mp4")
    if not audio_path:
        return jsonify({"error": "Failed to extract audio."}), 500

    transcript = transcribe_audio(audio_path)
    summary = simple_summarizer(transcript)

    # Save user history
    if 'user' in session:
        save_history(session['user'], "video_summarization", "Uploaded Video", summary)

    os.remove("uploaded_video.mp4")
    if os.path.exists(audio_path):
        os.remove(audio_path)

    return jsonify({"summary": summary})

# ---------------- MAIN ----------------

if __name__ == "__main__":
    app.run(debug=True)
