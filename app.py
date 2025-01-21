from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
from dotenv import load_dotenv
import os

app = Flask(__name__, static_folder='templates')
CORS(app)

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = api_key  # Use the key from .env file

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    audio_filename = request.form.get('filename')

    if not audio_filename or not audio_filename.endswith('.mp3'):
        return jsonify({'error': 'Invalid audio file format. Only MP3 files are allowed.'}), 400

    # Save and process the audio file
    audio_file.save(audio_filename)

    try:
        # Transcription
        with open(audio_filename, "rb") as f:
            transcription = openai.Audio.transcribe(
                model="whisper-1", 
                file=f,
            )
        text = transcription['text']

        # Categorization using GPT
        prompt = (f"Kategorisieren Sie den folgenden Text in ein einfaches gültiges JSON-Objekt (ohne mehrzeilige Python-Kommentare oder JSON-Wörter), das Folgendes enthält: Vorname, Nachname, Alter, Geschlecht, "
                    f"Blutdruck, Körpertemperatur und weitere Vitalparameter, Diagnosetext mit Nummer 1. bis Nummer 5. Diagnose als Javascript Array mit Key 1. etc. (numerischer Wert mit Punkt) Value: die Diagnose (text):\n\n{text}")
            
        # Using the chat completion method for ChatGPT 4.0 Mini model
        response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Use the ChatGPT 4.0 Mini model
                messages=[
                    {"role": "system", "content": "Sie sind ein hilfreicher Assistent, der auf medizinische Kategorisierung spezialisiert ist."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.5  # Adjust temperature for response creativity
            )
            
        # Extract the assistant's reply
        categories = response['choices'][0]['message']['content'].strip()
            
        return jsonify({'transcription': text, 'categories': categories})

    except Exception as e:
        return jsonify({'error': f"Error during GPT processing: {str(e)}"}), 500

    finally:
        # Clean up the saved audio file
        os.remove(audio_filename)

if __name__ == '__main__':
    app.run(debug=True)
