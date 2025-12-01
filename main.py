from fastapi import FastAPI
import yt_dlp
import os
import requests

app = FastAPI()

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
                                "label": "HD (With Sound)", 
                                "url": video_data.get("play", ""),
                                "headers": {"User-Agent": "Mozilla/5.0"}
                            }
                        ]
                    }
            except:
                pass

        # --- FB / INSTA LOGIC ---
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        cookie_file = "cookies.txt"
        if os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            available_qualities = []
            
            real_headers = info.get('http_headers', {})

            for f in formats:
                # CHECK: Video (mp4) HONA CHAHIYE + Audio (acodec) HONA CHAHIYE
                if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    height = f.get('height')
                    if height:
                        label = f"{height}p"
                        # Duplicate hatana
                        if not any(q['label'] == label for q in available_qualities):
                            available_qualities.append({
                                "label": label,
                                "url": f['url'],
                                "headers": real_headers
                            })
            
            # Agar filter ke baad kuch na bache, toh Best Combined uthao
            if not available_qualities:
                direct_url = info.get('url') or info['requested_downloads'][0]['url']
                available_qualities.append({
                    "label": "Standard Quality", 
                    "url": direct_url,
                    "headers": real_headers
                })

            # High Quality upar rakho
            available_qualities.sort(key=lambda x: int(x['label'].replace('p', '')) if 'p' in x['label'] else 0, reverse=True)

            return {
                "status": "success",
                "title": info.get('title', 'Social Video'),
                "thumbnail": info.get('thumbnail', None),
                "qualities": available_qualities
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}