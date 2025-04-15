import os
import base64
import random
import numpy as np
import cv2
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from keras.models import load_model
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from dotenv import load_dotenv
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

path = '/home/ChithaaMadanayake/mysite/flask_app.py'
if path not in sys.path:
    sys.path.insert(0, path)
from app import app as application

# Load environment variables
load_dotenv()
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")

# Azure speech setup
speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
speech_config.speech_synthesis_volume = "+100%"
synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

# Azure OpenAI setup
client = AzureOpenAI(
    azure_deployment="openai-base-demo-4o",
    api_version="2024-04-01-preview",
    api_key=AZURE_OPENAI_KEY,
    azure_endpoint="https://openai-base-demo.openai.azure.com"
)

# Emotion model
model = load_model('src/emotion_detector_models/model_v6_135.keras')
emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Neutral', 'Surprise']

# Set up music base folder
MUSIC_BASE = os.path.join(os.path.dirname(__file__), 'music')  # Separate folder for music

@app.route('/')
def home():
    return render_template('index.html')
# if __name__=='__main__':
#   app.run(debug=True)

@app.route('/detect-emotion', methods=['POST'])
def detect_emotion():
    try:
        # Get the data from the frontend
        data = request.json
        image_data = data.get('image')
        if not image_data:
            return jsonify(error='No image received'), 400

        # Decode and preprocess image
        nparr = np.frombuffer(base64.b64decode(image_data.split(',')[1]), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (48, 48)).astype('float32') / 255
        img = img.reshape((1, 48, 48, 1))

        # Predict emotion
        pred = model.predict(img)[0]
        detected_emotion = emotion_labels[np.argmax(pred)].capitalize()

        # Generate motivational message + speech synthesis
        motivational_message = generate_motivational_message(detected_emotion)
        speak_motivation(motivational_message, detected_emotion)

        # Select music based on emotion
        music_file = pick_music(detected_emotion)

        # Construct music URL
        if music_file:
            emotion_folder = music_file.split('/')[0]
            song_filename = music_file.split('/')[1]
            music_url = f"/music/{emotion_folder}/{song_filename}"
        else:
            music_url = ''

        # Logging the results for debugging
        print(f"Emotion: {detected_emotion}")
        print(f"Quote: {motivational_message}")
        print(f"Music: {music_url}")

        return jsonify(
            emotion=detected_emotion,
            message=motivational_message,
            music=music_url
        )
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(error="Something went wrong on server."), 500

# Generate a motivational message based on detected emotion
def generate_motivational_message(emotion):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a compassionate and empathetic listener."},
                      {"role": "user", "content": f"Give a short, heart-touching motivational quote for someone feeling {emotion.lower()}."}],
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "You are not alone in this. Take a deep breath, and know that brighter days are ahead. You’ve got this."

# Use text-to-speech to speak the motivational message
def speak_motivation(msg, emotion):
    try:
        if emotion.lower() == 'sad':
            speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
        synthesizer.speak_text_async(msg).get()
    except Exception as e:
        print(f"Speech Error: {e}")

# Select music based on emotion
def pick_music(emotion):
    valid_emotions = ['angry', 'sad', 'happy', 'surprise']
    emotion = emotion.lower()
    folder_path = os.path.join(MUSIC_BASE, emotion) if emotion in valid_emotions else None

    # If the folder for the specific emotion doesn't exist, pick a random folder
    if not folder_path or not os.path.isdir(folder_path):
        folders = [os.path.join(MUSIC_BASE, f) for f in os.listdir(MUSIC_BASE) if os.path.isdir(os.path.join(MUSIC_BASE, f))]
        if not folders:
            return ''  # No music found

        # Randomly choose a folder
        folder_path = random.choice(folders)

    # Get all music files (mp3 or wav)
    files = [f for f in os.listdir(folder_path) if f.endswith(('.mp3', '.wav'))]
    if not files:
        return ''  # No music files found

    # Return a random music file from the chosen folder
    return f"{os.path.basename(folder_path)}/{random.choice(files)}"



# Serve the music file from the music directory (outside of static)
@app.route('/music/<emotion>/<filename>')
def serve_music(emotion, filename):
    music_folder = os.path.join(MUSIC_BASE, emotion)
    return send_from_directory(music_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)
