from fastapi import FastAPI
import yt_dlp
import os
import requests

app = FastAPI()

@app.get("/download")
def download_video(url: str):
    try:
        # --- TIKTOK LOGIC (Ye already Fast hai) ---
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
                                "headers": {"User-Agent": "Mozilla/5.0"}
                            }
                        ]
                    }
            except:
                pass

        # --- FB / INSTA LOGIC (OPTIMIZED) ---
        
        # 1. Mobile User Agent use karein taake FB/Insta ko lage mobile se access ho raha hai (Faster speeds)
        mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': mobile_ua, # Change: Mobile UA for faster serving
            'socket_timeout': 10,    # Change: Agar 10 sec tak response na aye to hang na ho
            'retries': 3,            # Change: Fail hone par 3 baar retry kare
            'geo_bypass': True,      # Change: Region restriction hataye
            'format': 'best',        # Try to get best single file
        }
        
        cookie_file = "cookies.txt"
        if os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # download=False is important for API
            info = ydl.extract_info(url, download=False)
            
            # Agar formats available nahi hain (Sometimes happens with Reels)
            formats = info.get('formats', [info]) 
            available_qualities = []
            
            # Headers extract karein jo client ko bhejne hain
            real_headers = info.get('http_headers', {})
            # Ensure User-Agent same ho jo yt-dlp ne use kiya
            real_headers['User-Agent'] = mobile_ua 

            for f in formats:
                # Logic: MP4 ho + Video Codec ho + Audio Codec ho (Video with Sound)
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    
                    height = f.get('height')
                    # Fallback agar height na mile
                    if not height: 
                        height = f.get('width', 0)

                    label = f"{height}p" if height else "Standard"
                    
                    # Protocol check: m3u8 (HLS) links aksar mobile players mein slow chalte hain agar network unstable ho
                    # Koshish karein ke 'https' direct links uthayein
                    if 'm3u8' not in f['url']:
                        
                        # Duplicate hatana
                        if not any(q['label'] == label for q in available_qualities):
                            available_qualities.append({
                                "label": label,
                                "url": f['url'],
                                "headers": real_headers # IMPORTANT: Client ko ye headers sath bhejne honge
                            })
            
            # Agar loop se kuch na mile (Fallback logic)
            if not available_qualities:
                direct_url = info.get('url')
                if direct_url:
                    available_qualities.append({
                        "label": "SD Quality", 
                        "url": direct_url,
                        "headers": real_headers
                    })

            # Sorting: High Quality (e.g. 720p, 1080p) sabse upar
            available_qualities.sort(
                key=lambda x: int(x['label'].replace('p', '')) if x['label'] != "Standard" and x['label'] != "SD Quality" else 0, 
                reverse=True
            )

            return {
                "status": "success",
                "title": info.get('title', 'Social Video'),
                "thumbnail": info.get('thumbnail', None),
                "qualities": available_qualities
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}