from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Video Downloader API chal rahi hai!"}

@app.get("/download")
def download_video(url: str):
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Video info nikalna
            info = ydl.extract_info(url, download=False)
            
            return {
                "status": "success",
                "title": info.get('title', 'Unknown'),
                "thumbnail": info.get('thumbnail', None),
                "download_url": info.get('url', None)  # Direct video link
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}