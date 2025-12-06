"""
AWS Helper Functions
Handles S3 storage, Amazon Polly text-to-speech, and Cohere AI rephrasing.
"""
import os
import uuid
import boto3
import cohere
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Cohere Configuration
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
co = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')

# Local audio directory
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'static', 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)

# Try multiple regions for Polly
POLLY_REGIONS = ['eu-north-1', 'eu-west-1', 'eu-central-1', 'us-east-1']
polly_client = None

for region in POLLY_REGIONS:
    try:
        test_client = boto3.client('polly', region_name=region)
        # Test if we can access Polly in this region
        test_client.describe_voices(LanguageCode='en-US')
        polly_client = test_client
        print(f"✓ Polly connected in region: {region}")
        break
    except Exception as e:
        print(f"✗ Polly not available in {region}: {e}")

if polly_client is None:
    print("WARNING: Polly not available in any region")


def save_note(title, content):
    """
    Save a text note to S3.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    note_id = f"{timestamp}_{unique_id}"
    
    note_data = f"{title}\n---\n{content}"
    note_key = f"notes/{note_id}.txt"
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=note_key,
        Body=note_data.encode('utf-8'),
        ContentType='text/plain'
    )
    
    print(f"✓ Note saved to S3: {note_key}")
    return note_id


def list_notes():
    """
    List all saved notes from S3.
    """
    notes = []
    
    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='notes/'
        )
        
        if 'Contents' not in response:
            return notes
        
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('.txt'):
                note_id = key.replace('notes/', '').replace('.txt', '')
                
                try:
                    content_response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
                    content = content_response['Body'].read().decode('utf-8')
                    
                    parts = content.split('\n---\n', 1)
                    title = parts[0] if parts else 'Untitled'
                    body = parts[1] if len(parts) > 1 else content
                    preview = body[:80] + '...' if len(body) > 80 else body
                    
                except:
                    title = 'Untitled'
                    preview = 'Unable to load preview'
                
                notes.append({
                    'id': note_id,
                    'title': title,
                    'date': obj['LastModified'].isoformat(),
                    'preview': preview
                })
        
        notes.sort(key=lambda x: x['date'], reverse=True)
        
    except Exception as e:
        print(f"Error listing notes: {e}")
    
    return notes


def get_note_content(note_id):
    """
    Get the full content of a specific note.
    """
    note_key = f"notes/{note_id}.txt"
    
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=note_key)
    content = response['Body'].read().decode('utf-8')
    
    parts = content.split('\n---\n', 1)
    title = parts[0] if parts else 'Untitled'
    body = parts[1] if len(parts) > 1 else content
    
    return {'title': title, 'content': body}


def delete_note(note_id):
    """
    Delete a note from S3 and local audio.
    """
    note_key = f"notes/{note_id}.txt"
    
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=note_key)
    except:
        pass
    
    # Delete local audio
    local_path = os.path.join(AUDIO_DIR, f"{note_id}.mp3")
    if os.path.exists(local_path):
        os.remove(local_path)


def rephrase_as_podcast(title, content):
    """
    Use Cohere AI to rephrase note content as a podcast-style narration.
    """
    if co is None:
        print("Cohere not configured, using fallback template")
        return f"""Welcome to your personal notes podcast. 
Today's note is titled: {title}.
Here's what you wrote:
{content}
That's all for this note. Thank you for listening!"""
    
    try:
        message = f"""Rephrase the following note as a friendly, engaging podcast narration. 
Make it sound natural and conversational, like a podcast host speaking to their audience.
Keep it concise but warm. Include a brief intro and outro.
Only output the podcast script, nothing else.

Note Title: {title}
Note Content: {content}"""

        response = co.chat(
            model='command-a-03-2025',
            message=message
        )
        
        podcast_text = response.text.strip()
        print(f"✓ Cohere rephrased the note as podcast")
        return podcast_text
        
    except Exception as e:
        print(f"Cohere error, using fallback: {e}")
        # Fallback to simple template
        return f"""Welcome to your personal notes podcast. 
Today's note is titled: {title}.
Here's what you wrote:
{content}
That's all for this note. Thank you for listening!"""


def text_to_speech(note_id, text, title="Your Note"):
    """
    Convert text to speech using Amazon Polly.
    Uses caching - if audio exists, returns cached version.
    Rephrases as podcast style first.
    Saves audio locally and to S3.
    
    Returns:
        Local URL path for the audio file
    """
    local_path = os.path.join(AUDIO_DIR, f"{note_id}.mp3")
    local_url = f"/static/audio/{note_id}.mp3"
    
    # Check cache - if audio already exists, return it
    if os.path.exists(local_path):
        print(f"✓ Using cached audio: {local_path}")
        return local_url
    
    if polly_client is None:
        raise Exception("Polly service not available. Check AWS credentials and region.")
    
    # Rephrase as podcast
    podcast_text = rephrase_as_podcast(title, text)
    
    print(f"Generating podcast for note: {note_id}")
    print(f"Text length: {len(podcast_text)} characters")
    
    # Generate speech with Polly
    response = polly_client.synthesize_speech(
        Text=podcast_text,
        OutputFormat='mp3',
        VoiceId='Amy'
    )
    
    audio_data = response['AudioStream'].read()
    print(f"✓ Polly generated {len(audio_data)} bytes of audio")
    
    # Save locally (cache)
    with open(local_path, 'wb') as f:
        f.write(audio_data)
    print(f"✓ Audio cached locally: {local_path}")
    
    # Also save to S3
    try:
        audio_key = f"audio/{note_id}.mp3"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=audio_key,
            Body=audio_data,
            ContentType='audio/mpeg'
        )
        print(f"✓ Audio saved to S3: {audio_key}")
    except Exception as e:
        print(f"Warning: Could not save to S3: {e}")
    
    # Return local URL (served by Flask)
    return local_url
