import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import speech_recognition as sr
from pydub import AudioSegment
import tempfile

app = Flask(__name__)
CORS(app)

# Store audio transcriptions
transcriptions = []

@app.route('/')
def index():
    return render_template('index.html', transcriptions=transcriptions)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    recognizer = sr.Recognizer()

    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_audio:
            temp_path = temp_audio.name
            audio_file.save(temp_path)

        # Convert to WAV if necessary
        if not temp_path.lower().endswith('.wav'):
            audio = AudioSegment.from_file(temp_path)
            wav_path = tempfile.mktemp(suffix='.wav')
            audio.export(wav_path, format="wav")
            os.unlink(temp_path)
            temp_path = wav_path

        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)

        # Perform the transcription
        text = recognizer.recognize_google(audio)

        # Add to transcriptions
        transcriptions.insert(0, text)  # Add new transcription at the beginning

        # Clean up the temporary file
        os.unlink(temp_path)

        return jsonify({'text': text})
    except sr.UnknownValueError:
        return jsonify({'error': 'Unable to recognize speech'}), 400
    except sr.RequestError as e:
        return jsonify({'error': f'Error processing the request: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/download/<int:index>')
def download(index):
    if 0 <= index < len(transcriptions):
        text = transcriptions[index]
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(text)
            temp_file_path = temp_file.name
        return send_file(temp_file_path, as_attachment=True, download_name='transcription.txt')
    else:
        return jsonify({'error': 'Invalid transcription index'}), 400

if __name__ == '__main__':
    app.run(debug=True)