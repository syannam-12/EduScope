import os
import requests
# from moviepy.editor import VideoFileClip
import speech_recognition as sr
from pytube import YouTube
from flask import Flask, request, jsonify, render_template
import yt_dlp
import subprocess
import os
from youtubesearchpython import VideosSearch
import contextlib
import yt_dlp



app = Flask(__name__)

# --- Helper Functions ---


from yt_dlp import YoutubeDL

def search_youtube_video(query, max_duration=100):
    try:
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'extract_flat': 'in_playlist',
            'default_search': 'ytsearch10',
            'force_generic_extractor': False,
        }
        with YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            print(search_result)
            for entry in search_result['entries']:
                if entry.get('duration') and entry['duration'] <= max_duration:
                    return entry['url']  # return direct video URL
            # if search_result and 'entries' in search_result and len(search_result['entries']) > 0:
            #     video_info = search_result['entries'][0]
            #     return video_info.get("webpage_url")
            else:
                print("No entries found.")
                return None
    except Exception as e:
        print(f"Error in YouTube search: {e}")
        return None


def download_youtube_video(url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'video_audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "video_audio.wav"
    except Exception as e:
        print("Error downloading YouTube video:", e)
        return None

def download_video_from_url(url):
    try:
        response = requests.get(url, stream=True)
        file_path = "downloaded_video.mp4"
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        return file_path
    except Exception as e:
        print("URL download error:", e)
        return None

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Error with Google Speech API: {e}"

def simple_summarizer(text, max_sentences=3):
    sentences = text.split('.')
    return '. '.join(sentences[:max_sentences]).strip() + '.'


# --- Flask Routes ---

@app.route("/")
def home():
    return render_template("vindexold.html")

@app.route("/summarize-text", methods=["POST"])
def summarize_text():
    data = request.get_json()
    if "topic" in data:
        topic = data["topic"]
        # TODO: You can add Google Search + Wikipedia scraper here
        dummy_text = f"Summary about {topic}: Lorem ipsum dolor sit amet, consectetur adipiscing elit."
        return jsonify({"summary": simple_summarizer(dummy_text)})

    elif "url" in data:
        url = data["url"]
        try:
            content = requests.get(url).text
            return jsonify({"summary": simple_summarizer(content)})
        except Exception as e:
            return jsonify({"error": f"Error fetching content: {e}"})
    else:
        return jsonify({"error": "Invalid input."})

@app.route("/summarize-video-url", methods=["POST"])
def summarize_video_url():
    video_url_or_text = request.form.get("url")
    if not video_url_or_text:
        return jsonify({"error": "No video URL or search text provided."}), 400

    # Check if direct video URL
    if "youtube.com" in video_url_or_text or "youtu.be" in video_url_or_text:
        used_video_url = video_url_or_text
    else:
        used_video_url = search_youtube_video(video_url_or_text)
        if not used_video_url:
            return jsonify({"error": "Failed to search YouTube for the given text."}), 500

    # Download the actual video
    video_path = download_youtube_video(used_video_url)
    if not video_path:
        return jsonify({"error": "Failed to download video."}), 500

    transcript = transcribe_audio("video_audio.wav")
    summary = simple_summarizer(transcript)

    os.remove(video_path)
    # os.remove("video_audio.wav") # Uncomment if needed

    return jsonify({
        "searched_text": video_url_or_text,
        "video_used": used_video_url,
        "summary": summary
    })

def extract_audio(video_path):
    try:
        audio_path = "video_audio.wav"
        
        # If you have ffmpeg in PATH, no need to give full path
        # Otherwise, use: ffmpeg_path = r"C:\path\to\ffmpeg.exe"
        ffmpeg_command = [
            "ffmpeg",
            "-i", video_path,
            "-vn",                  # no video
            "-acodec", "pcm_s16le", # WAV format
            "-ar", "16000",         # sampling rate for speech models
            "-ac", "1",             # mono channel
            audio_path,
            "-y"                    # overwrite if file exists
        ]
        subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        if os.path.exists(audio_path):
            return audio_path
        else:
            return None
    except Exception as e:
        print("Audio extraction error:", str(e))
        return None


@app.route("/summarize-video", methods=["POST"])
def summarize_video():
    if "file" not in request.files:
        return jsonify({"error": "No video file uploaded."}), 400

    video_file = request.files["file"]
    video_path = "uploaded_video.mp4"
    video_file.save(video_path)

    # FFMPEG-only extraction
    audio_path = extract_audio(video_path)
    if not audio_path or not os.path.exists(audio_path):
        return jsonify({"error": "Failed to extract audio."}), 500

    transcript = transcribe_audio(audio_path)
    summary = simple_summarizer(transcript)

    # Clean up
    with contextlib.suppress(Exception): os.remove(video_path)
    with contextlib.suppress(Exception): os.remove(audio_path)

    return jsonify({"summary": summary})



if __name__ == "__main__":
    app.run(debug=True)
