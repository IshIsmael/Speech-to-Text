from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import speech_recognition as sr
import os
import tempfile
import wave
import io

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
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio_path = temp_audio.name
            audio_file.save(temp_audio_path)
        
        with sr.AudioFile(temp_audio_path) as source:
            audio = recognizer.record(source)
        
        os.unlink(temp_audio_path)  # Delete the temporary file

        text = recognizer.recognize_google(audio)
        transcriptions.append(text)
        return jsonify({'text': text})
    except sr.UnknownValueError:
        return jsonify({'error': 'Unable to recognize speech'}), 400
    except sr.RequestError as e:
        return jsonify({'error': f'Error processing the request: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        # Ensure the temporary file is deleted even if an error occurs
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except Exception as e:
                print(f"Error deleting temporary file: {str(e)}")

@app.route('/download/<int:index>')
def download(index):
    if 0 <= index < len(transcriptions):
        text = transcriptions[index]
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(text)
            temp_file_path = temp_file.name
        return send_file(temp_file_path, as_attachment=True, attachment_filename='transcription.txt')
    else:
        return jsonify({'error': 'Invalid transcription index'}), 400

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)