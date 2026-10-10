# youtube-auto-uploader

A Python script to upload standard videos to YouTube with customizable metadata and privacy settings via the YouTube Data API v3.

## How it works

1. Authenticates using local OAuth (`client_secrets.json` / `token.json`).
2. Takes a video file, title, description, tags, category, and privacy level (`public`, `private`, `unlisted`).
3. Uploads the file via YouTube Data API v3 using 5MB resumable chunks.
4. Outputs the final video link (`https://youtu.be/<id>`).

## Usage

```bash
pip install -r requirements.txt
python main.py --file "video.mp4" --title "My Video" --privacy "public"
```
