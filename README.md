# Text Note Saver with Voice Playback

A simple web application that saves text notes to AWS S3 and converts them to speech using Amazon Polly.

## AWS Services Used

1. **Amazon S3** - Stores text notes and generated audio files
2. **Amazon Polly** - Converts notes to natural-sounding speech

## Features

- Create and save text notes
- Notes stored in S3 bucket
- Click any note to view full content
- Listen to notes using Amazon Polly text-to-speech
- Delete notes when no longer needed

## AWS Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://voice-notes-cs504 --region eu-north-1
```

### 2. Configure IAM Permissions

Create an IAM user or role with these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::voice-notes-cs504",
                "arn:aws:s3:::voice-notes-cs504/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "polly:SynthesizeSpeech"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Configure AWS Credentials

```bash
aws configure
# Enter your Access Key ID, Secret Key, and region (eu-north-1)
```

### 4. Create .env File

Create a `.env` file in the project root:

```
AWS_REGION=eu-north-1
S3_BUCKET=voice-notes-cs504
COHERE_API_KEY=your_cohere_api_key
```

## Installation

1. Create virtual environment:
```bash
cd project_cs504
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the App

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Usage

1. Type a note in the text area
2. Click "Save Note" to store it in S3
3. Click any note to view full content
4. Click "Listen" to hear the note read aloud (using Polly)
5. Click "Delete" to remove a note

## Cost

AWS Free Tier includes:
- 5GB S3 storage
- 5 million Polly characters/month (first 12 months)

## Project Structure

```
project_cs504/
├── app.py              # Flask backend
├── transcribe.py       # AWS S3 & Polly functions
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Frontend page
└── static/
    └── style.css       # Styling
```
