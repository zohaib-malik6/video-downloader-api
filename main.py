from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- IMPORT THIS
import yt_dlp
import os
import requests

app = FastAPI()

# --- CORS SETTINGS (BOHT ZAROORI HAI) ---
# Iske baghair React app API se baat nahi kar payega
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Filhal sab allow kar rahe hain (Production mein apni site ka link dein)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API is running!"}

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
            
            # Simple Logic for Frontend
            for f in formats:
                # Video with Sound (mp4)
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    height = f.get('height')
                    if not height: height = f.get('width', 0)
                    label = f"{height}p" if height else "Standard"
                    
                    # Avoid m3u8 for direct download buttons if possible
                    if 'm3u8' not in f['url']:
                        # Duplicate check
                        if not any(q['label'] == label for q in available_qualities):
                            available_qualities.append({
                                "label": label,
                                "url": f['url'],
                                "size": "MP4"
                            })
            
            # Fallback
            if not available_qualities:
                direct_url = info.get('url')
                if direct_url:
                    available_qualities.append({
                        "label": "Download Video", 
                        "url": direct_url,
                        "size": "Source"
                    })

            # Sort High to Low
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