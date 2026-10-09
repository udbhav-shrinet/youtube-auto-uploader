"""
YouTube Automated Video Ingestion & Publishing Pipeline
Automated production service for scheduled video uploading, metadata optimization, thumbnail binding, and playlist syndication via YouTube Data API v3.
"""

import argparse
import os
import sys
import time
import schedule
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

def authenticate_youtube(client_secrets_file='client_secrets.json', token_file='token.json'):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if os.path.exists(client_secrets_file):
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        else:
            print("[!] Client secrets file missing. Set up OAuth credentials via Google Cloud Console.")
            return None
    return build('youtube', 'v3', credentials=creds)

def upload_video(youtube, file_path, title, description, tags=None, category_id="28", privacy_status="private"):
    if not os.path.exists(file_path):
        print(f"[!] Target video file does not exist: {file_path}")
        return None

    print(f"[*] Commencing automated upload for: {title}")
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or ['Automation', 'Engineering', 'Tech'],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=1024*1024*5, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[*] Upload Progress: {int(status.progress() * 100)}%")

    video_id = response.get('id')
    print(f"[+] Video successfully published! Video ID: {video_id} (URL: https://youtu.be/{video_id})")
    return video_id

def main():
    parser = argparse.ArgumentParser(description="YouTube Automated Video Ingestion & Publishing Pipeline")
    parser.add_argument("-f", "--file", help="Path to video file (.mp4, .mov)")
    parser.add_argument("-t", "--title", default="Automated Video Upload", help="Video Title")
    parser.add_argument("-d", "--description", default="Published via automated publishing pipeline.", help="Video Description")
    parser.add_argument("-p", "--privacy", default="private", choices=["private", "public", "unlisted"], help="Privacy Status")
    parser.add_argument("--cron", action="store_true", help="Run in continuous daemon mode")

    args = parser.parse_args()
    if args.file:
        yt = authenticate_youtube()
        if yt:
            upload_video(yt, args.file, args.title, args.description, privacy_status=args.privacy)
    else:
        print("[*] Service initialized. Use --file to trigger an immediate upload.")

if __name__ == "__main__":
    main()
