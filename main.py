from fastapi import FastAPI, HTTPException
import yt_dlp
import os

app = FastAPI()

@app.get("/")
def home():
    return {"message": "All-in-One Video Downloader API Running"}

@app.get("/download")
def download_video(url: str):
    try:
        # Default Settings
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }

        # --- LOGIC: TikTok vs Others ---
        
        if "tiktok.com" in url:
            # TikTok ke liye: Cookies MAT use karein, lekin Mobile User Agent lagayein
            # Kyunki TikTok server IPs ko jaldi block karta hai agar desktop agent ho
            ydl_opts['user_agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        
        else:
            # Facebook/Instagram ke liye: Cookies Zaroori hain
            cookie_file = "cookies.txt"
            if os.path.exists(cookie_file):
                ydl_opts['cookiefile'] = cookie_file
            
            # Inke liye Desktop Agent use karein
            ydl_opts['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

        # --- DOWNLOAD PROCESS ---
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # TikTok kabhi kabhi direct URL nahi deta, format check karna padta hai
            video_url = info.get('url', None)
            
            # Agar direct URL na mile toh requested_downloads check karein
            if not video_url and 'requested_downloads' in info:
                video_url = info['requested_downloads'][0]['url']

            return {
                "status": "success",
                "title": info.get('title', 'Social Video'),
                "thumbnail": info.get('thumbnail', None),
                "download_url": video_url
            }

    except Exception as e:
        # Error log return karein taaki hum debug kar sakein
        return {"status": "error", "message": str(e)}