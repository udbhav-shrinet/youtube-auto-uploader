import os
import pickle
import requests # New library
from moviepy.editor import VideoFileClip # New library
import praw
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.cloud import storage
import functions_framework
from uuid import uuid4

# --- Configuration ---
BUCKET_NAME = "pickle123"
REDDIT_CLIENT_ID = "xiKwPOI6DE87ZB-IAxVlOA"
REDDIT_CLIENT_SECRET = "24ObWXWFU0ZlN5pJoiQ344vdXan4Ag"
REDDIT_USER_AGENT = "wholesome_reel_uploader_v3"

# Reddit setup
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# (Your download_youtube_token and get_youtube_credentials functions remain the same)
# ...

@functions_framework.cloud_event
def pubsub_handler(cloud_event):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    filename = None 

    try:
        # 1. Get credentials and previously uploaded IDs
        download_youtube_token()
        creds = get_youtube_credentials()
        uploaded_ids_blob = bucket.blob("uploaded_ids.txt")
        uploaded_ids = set(uploaded_ids_blob.download_as_text().splitlines() if uploaded_ids_blob.exists() else [])
        print(f"Found {len(uploaded_ids)} previously uploaded post IDs.")

        # 2. Find a new video from Reddit
        subreddits = ["MadeMeSmile", "aww", "ContagiousLaughter", "wholesomegifs"]
        video_post = None
        
        print("Searching for a new video...")
        for sub in subreddits:
            for post in reddit.subreddit(sub).hot(limit=25):
                if post.is_video and not post.over_18 and post.id not in uploaded_ids:
                    video_post = post
                    break
            if video_post:
                break

        if not video_post:
            print("No new, suitable video found.")
            return "No new video found."

        print(f"Found new video: '{video_post.title}' (ID: {video_post.id})")

        # 3. Download the video file directly using requests
        video_url = video_post.media['reddit_video']['fallback_url']
        filename = f"/tmp/{uuid4().hex}.mp4"
        
        print(f"Downloading video directly from: {video_url}")
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)

        # 4. Check for an audio track using moviepy
        print("Checking for audio track...")
        with VideoFileClip(filename) as clip:
            if clip.audio is None:
                print("❌ Video has no audio. Skipping this post.")
                # Add to uploaded list to avoid re-checking this silent video
                uploaded_ids.add(video_post.id)
                uploaded_ids_blob.upload_from_string('\n'.join(uploaded_ids))
                return "Skipped silent video."
        
        print("✅ Audio track found.")

        # 5. Upload to YouTube
        youtube = build("youtube", "v3", credentials=creds)
        request_body = {
            'snippet': {
                'title': video_post.title[:100],
                'description': f"Credit to u/{video_post.author} on Reddit.\nOriginal post: https://www.reddit.com{video_post.permalink}\n\n#shorts #reddit #wholesome",
                'tags': ['reddit', 'shorts', 'wholesome', video_post.subreddit.display_name],
                'categoryId': '24' 
            },
            'status': {'privacyStatus': 'public'}
        }
        
        media = MediaFileUpload(filename, resumable=True)
        print("Uploading to YouTube...")
        youtube.videos().insert(part="snippet,status", body=request_body, media_body=media).execute()
        
        print(f"✅ Upload successful for post ID: {video_post.id}")

        # 6. Update tracking file
        uploaded_ids.add(video_post.id)
        uploaded_ids_blob.upload_from_string('\n'.join(uploaded_ids))
        print("Updated tracking file.")

    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)
        print("Function execution finished.")

    return "Function executed."

# You still need your download_youtube_token and get_youtube_credentials functions here
def download_youtube_token():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("youtube_token.pickle")
    os.makedirs("/tmp/.credentials", exist_ok=True)
    token_path = "/tmp/.credentials/youtube_token.pickle"
    blob.download_to_filename(token_path)

def get_youtube_credentials():
    token_path = '/tmp/.credentials/youtube_token.pickle'
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token_file:
            creds = pickle.load(token_file)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            with open(token_path, 'wb') as token_file:
                pickle.dump(creds, token_file)
        else:
            raise Exception("YouTube credentials are not valid and cannot be refreshed.")
    return creds
