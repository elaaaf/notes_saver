"""
Text Note Saver with Voice Playback - Flask Backend
Uses S3 for storage and Polly for text-to-speech.
"""
from flask import Flask, render_template, request, jsonify
from transcribe import (
    save_note,
    list_notes,
    get_note_content,
    delete_note,
    text_to_speech
)

app = Flask(__name__)


@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/notes', methods=['GET', 'POST'])
def notes():
    """Get all notes or create a new note."""
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if not title:
            title = content[:30] + '...' if len(content) > 30 else content
        
        try:
            note_id = save_note(title, content)
            return jsonify({'success': True, 'id': note_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:
        try:
            notes_list = list_notes()
            return jsonify({'notes': notes_list})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/notes/<note_id>', methods=['GET', 'DELETE'])
def note_detail(note_id):
    """Get or delete a specific note."""
    if request.method == 'DELETE':
        try:
            delete_note(note_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:
        try:
            note = get_note_content(note_id)
            return jsonify(note)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/speak/<note_id>', methods=['POST'])
def speak_note(note_id):
    """Convert note to podcast-style speech using Amazon Polly."""
    try:
        note = get_note_content(note_id)
        print(f"Converting note to podcast: {note_id}")
        audio_url = text_to_speech(note_id, note['content'], note['title'])
        print(f"Audio URL generated: {audio_url}")
        return jsonify({'success': True, 'audio_url': audio_url})
    except Exception as e:
        print(f"Error in speak_note: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
