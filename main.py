from fastapi import FastAPI
import yt_dlp
import os
import requests  # Nayi library TikTok ke liye

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Universal Video Downloader API is Running"}

@app.get("/download")
def download_video(url: str):
    try:
        # -----------------------------------------------
        # LOGIC 1: AGAR TIKTOK HAI TOH "TikWM" USE KARO
        # -----------------------------------------------
        if "tiktok.com" in url:
            try:
                # TikWM Free API call
                response = requests.post("https://www.tikwm.com/api/", data={"url": url})
                data = response.json()
                
                if data.get("code") == 0:  # 0 ka matlab Success
                    video_data = data["data"]
                    return {
                        "status": "success",
                        "title": video_data.get("title", "TikTok Video"),
                        "thumbnail": video_data.get("cover", ""),
                        "download_url": video_data.get("play", ""),  # Direct Video Link (No Watermark)
                        "source": "TikWM"
                    }
                else:
                    return {"status": "error", "message": "TikTok API Failed"}
            except Exception as e:
                return {"status": "error", "message": f"TikTok Error: {str(e)}"}

        # -----------------------------------------------
        # LOGIC 2: AGAR FB/INSTA HAI TOH "yt-dlp" USE KARO
        # -----------------------------------------------
        
        # Cookies check
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Sirf FB/Insta ke liye cookies lagayen
        cookie_file = "cookies.txt"
        if os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Direct URL nikalna
            video_url = info.get('url', None)
            
            # Agar direct URL na mile (kabhi kabhi format alag hota hai)
            if not video_url and 'requested_downloads' in info:
                video_url = info['requested_downloads'][0]['url']

            return {
                "status": "success",
                "title": info.get('title', 'Social Video'),
                "thumbnail": info.get('thumbnail', None),
                "download_url": video_url,
                "source": "yt-dlp"
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}