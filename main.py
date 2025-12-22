from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from urllib.parse import quote  # <--- 1. YEH IMPORT ADD KAREIN
import yt_dlp
import os
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API is running!"}

# --- UPDATED STREAM ENDPOINT (Encoding Fix) ---
@app.get("/stream")
def stream_video(url: str, title: str = "video"):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        external_req = requests.get(url, stream=True, headers=headers)
        
        def iterfile():
            for chunk in external_req.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        # --- 2. YAHAN CHANGE KIYA HAI (Latin-1 Fix) ---
        # Filename ko safe banaya taake Emojis/Urdu se crash na ho
        # Hum 'quote' use kar rahe hain jo special chars ko %20 type mein convert krdega
        
        safe_filename = quote(f"{title}.mp4") 
        
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            # filename* use karne se browser UTF-8 (Urdu/Emojis) samajh jata hai
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{safe_filename}"}
        )
    except Exception as e:
        return {"error": str(e)}

@app.get("/download")
def download_video(url: str):
    try:
        # --- TIKTOK LOGIC ---
        if "tiktok.com" in url:
            try:
                response = requests.post("https://www.tikwm.com/api/", data={"url": url})
                data = response.json()
                if data.get("code") == 0:
                    video_data = data["data"]
                    return {
                        "status": "success",
                        "title": video_data.get("title", "TikTok Video"),
                        "thumbnail": video_data.get("cover", ""),
                        "qualities": [
                            {
                                "label": "HD (No Watermark)", 
                                "url": video_data.get("play", ""),
                                "size": "HD"
                            },
                             {
                                "label": "Music (MP3)", 
                                "url": video_data.get("music", ""),
                                "size": "Audio"
                            }
                        ]
                    }
            except Exception as e:
                print("TikTok Error:", str(e))
                pass

        # --- FB / INSTA / YOUTUBE LOGIC ---
        mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': mobile_ua,
            'socket_timeout': 15,
            'retries': 3,
            'geo_bypass': True,
            'format': 'best',
        }
        
        cookie_file = "cookies.txt"
        if os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get('formats', [info]) 
            available_qualities = []
            
            for f in formats:
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    height = f.get('height')
                    if not height: height = f.get('width', 0)
                    label = f"{height}p" if height else "Standard"
                    
                    if 'm3u8' not in f['url']:
                        if not any(q['label'] == label for q in available_qualities):
                            available_qualities.append({
                                "label": label,
                                "url": f['url'],
                                "size": "MP4"
                            })
            
            if not available_qualities:
                direct_url = info.get('url')
                if direct_url:
                    available_qualities.append({
                        "label": "Download Video", 
                        "url": direct_url,
                        "size": "Source"
                    })

            available_qualities.sort(
                key=lambda x: int(x['label'].replace('p', '')) if 'p' in x['label'] else 0, 
                reverse=True
            )

            return {
                "status": "success",
                "title": info.get('title', 'Social Video'),
                "thumbnail": info.get('thumbnail', None),
                "duration": info.get('duration_string', 'N/A'),
                "qualities": available_qualities
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}