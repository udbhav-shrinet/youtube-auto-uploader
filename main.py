import os
import pickle
import yt_dlp
import praw
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.cloud import storage
import functions_framework
from uuid import uuid4

# --- Configuration ---
# ⚠️ Security Warning: For a real application, do not hardcode secrets like these.
# Use Google Cloud Secret Manager to store them securely.
BUCKET_NAME = "pickle123"  # Your GCS bucket name
REDDIT_CLIENT_ID = "xiKwPOI6DE87ZB-IAxVlOA"
REDDIT_CLIENT_SECRET = "24ObWXWFU0ZlN5pJoiQ344vdXan4Ag"
REDDIT_USER_AGENT = "wholesome_reel_uploader_v2"

# Reddit setup
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def download_youtube_token():
    """Downloads the YouTube token from GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("youtube_token.pickle")
    os.makedirs("/tmp/.credentials", exist_ok=True)
    token_path = "/tmp/.credentials/youtube_token.pickle"
    blob.download_to_filename(token_path)

def get_youtube_credentials():
    """Refreshes and returns YouTube credentials."""
    token_path = '/tmp/.credentials/youtube_token.pickle'
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token_file:
            creds = pickle.load(token_file)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            # Save the refreshed credentials back to the file
            with open(token_path, 'wb') as token_file:
                pickle.dump(creds, token_file)
        else:
            raise Exception("YouTube credentials are not valid and cannot be refreshed.")
    return creds

@functions_framework.cloud_event
def pubsub_handler(cloud_event):
    """
    This function is triggered by a Pub/Sub message.
    It finds a new video, downloads it with audio, and uploads it to YouTube.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    filename = None # Define filename here for the finally block

    try:
        # 1. Get YouTube credentials
        download_youtube_token()
        creds = get_youtube_credentials()

        # 2. Get list of already uploaded post IDs from Cloud Storage
        uploaded_ids_blob = bucket.blob("uploaded_ids.txt")
        uploaded_ids = set()
        if uploaded_ids_blob.exists():
            uploaded_ids = set(uploaded_ids_blob.download_as_text().splitlines())
        print(f"Found {len(uploaded_ids)} previously uploaded post IDs.")

        # 3. Find a NEW video from Reddit
        subreddits = ["MadeMeSmile", "aww", "ContagiousLaughter", "wholesomegifs"]
        video_post = None
        
        print("Searching for a new video on Reddit...")
        for sub in subreddits:
            for post in reddit.subreddit(sub).hot(limit=25):
                if post.is_video and not post.over_18 and post.id not in uploaded_ids:
                    video_post = post
                    break
            if video_post:
                break

        if not video_post:
            print("No new, suitable video found this time.")
            return "No new video found."

        print(f"Found new video: '{video_post.title}' (ID: {video_post.id})")

        # 4. Download the video WITH AUDIO
        video_url = video_post.media['reddit_video']['fallback_url']
        filename = f"/tmp/{uuid4().hex}.mp4"
        
        ydl_opts = {
            'verbose': True,  # <-- ADD THIS LINE
            "outtmpl": filename,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4"
        }
        
        print(f"Downloading with audio: {video_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # 5. Upload to YouTube
        youtube = build("youtube", "v3", credentials=creds)
        
        request_body = {
            'snippet': {
                'title': video_post.title[:100],
                'description': f"Credit to u/{video_post.author} on Reddit.\nOriginal post: https://www.reddit.com{video_post.permalink}\n\n#shorts #reddit #wholesome",
                'tags': ['reddit', 'shorts', 'wholesome', video_post.subreddit.display_name],
                'categoryId': '24' # Entertainment
            },
            'status': {'privacyStatus': 'public'}
        }
        
        media = MediaFileUpload(filename, resumable=True)
        
        print("Uploading to YouTube...")
        youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        ).execute()
        
        print(f"✅ Upload successful for post ID: {video_post.id}")

        # 6. Add the new ID to our tracking file and save it back to Cloud Storage
        uploaded_ids.add(video_post.id)
        uploaded_ids_blob.upload_from_string('\n'.join(uploaded_ids))
        print(f"Updated tracking file.")

    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    finally:
        # Clean up the downloaded video file
        if filename and os.path.exists(filename):
            os.remove(filename)
        print("Function execution finished.")

    return "Function executed."
