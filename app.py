import yt_dlp
import os

def fetch_video_details(url):
    """
    Fetches video details and progressive mp4 formats using yt-dlp.
    Returns a dictionary with video info and progressive formats only.
    """
    ydl_opts = {"quiet": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        return {"error": f"Failed to fetch video: {e}"}

    video_details = {
        "title": info.get('title'),
        "uploader": info.get('uploader'),
        "duration": info.get('duration'),
        "views": info.get('view_count'),
        "formats": []
    }

    for f in info.get('formats', []):
        if f.get('ext') == 'mp4' and f.get('acodec') != 'none':  # progressive check
            video_details["formats"].append({
                "format_id": f.get('format_id'),
                "resolution": f.get('height'),
                "fps": f.get('fps'),
                "filesize_mb": round(f.get('filesize_approx', 0)/(1024*1024), 2) if f.get('filesize_approx') else None,
                "note": f.get('format_note'),
            })

    return video_details

def download_video(url, format_id, output_dir=None):
    """
    Downloads the selected progressive video.
    """
    ydl_opts = {
        "format": f"{format_id}",  # progressive already has audio
        "outtmpl": os.path.join(output_dir if output_dir else ".", "%(title)s.%(ext)s")
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Download complete!")
    except Exception as e:
        print(f"❌ Download failed: {e}")


# ----------------- Main ----------------- #
if __name__ == "__main__":
    url = input("Enter YouTube URL: ").strip()
    details = fetch_video_details(url)

    if "error" in details:
        print(details["error"])
    else:
        print(f"\nTitle: {details['title']}")
        print(f"Uploader: {details['uploader']}")
        print(f"Duration: {details['duration']} seconds")
        print(f"Views: {details['views']}\n")

        if not details["formats"]:
            print("⚠ No progressive mp4 formats available!")
        else:
            print("Available progressive mp4 formats:")
            for f in details["formats"]:
                print(f"  format_id: {f['format_id']}, res: {f['resolution']}p, fps: {f['fps']}, size: {f['filesize_mb']} MB, note: {f['note']}")

            chosen_id = input("\nEnter format_id to download: ").strip()
            folder = input("Enter download folder (leave empty for current folder): ").strip()
            download_video(url, chosen_id, folder if folder else None)
