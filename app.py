from flask import Flask, request, render_template, send_file, redirect, url_for
import yt_dlp
import os
import tempfile
import shutil
import time
from functools import wraps

app = Flask(__name__)

COOKIE_FILE = "cookies.txt"

# Simple in-memory cache: video_url -> info (just for duration of service)
cache = {}

def timeout(seconds=20):
    """Simple timeout decorator for functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            if elapsed > seconds:
                raise TimeoutError(f"Operation took too long ({elapsed:.1f}s)")
            return result
        return wrapper
    return decorator

def get_ydl_opts(format_id=None, download=False, tmpdir=None):
    opts = {
        "quiet": True,
        "cookiefile": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        "nocheckcertificate": True,
    }
    if format_id:
        opts["format"] = format_id
    if download and tmpdir:
        opts["outtmpl"] = os.path.join(tmpdir, "%(title)s.%(ext)s")
    return {k: v for k, v in opts.items() if v is not None}

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    info = None
    formats = []

    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            error = "Please enter a URL"
        else:
            try:
                # Check cache first
                if url in cache:
                    info = cache[url]
                else:
                    # Fetch info with timeout
                    @timeout(seconds=25)
                    def fetch_info(u):
                        ydl_opts = get_ydl_opts()
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            return ydl.extract_info(u, download=False)
                    
                    info = fetch_info(url)
                    # Cache it
                    cache[url] = info

                # Filter progressive mp4 formats
                for f in info.get('formats', []):
                    if (f.get('ext') == 'mp4' and
                        f.get('acodec') != 'none' and
                        f.get('vcodec') != 'none'):
                        formats.append({
                            "format_id": f["format_id"],
                            "resolution": f.get("height", "N/A"),
                            "filesize": round((f.get("filesize") or f.get("filesize_approx") or 0) / (1024*1024), 2)
                        })
                        # Limit number of formats to avoid long listing loops
                        if len(formats) >= 5:
                            break

                if not formats:
                    error = "No progressive mp4 formats available for this video."

            except TimeoutError as te:
                error = f"Operation timed out: {te}"
            except Exception as e:
                error = f"Error fetching video info: {e}"

    return render_template("index.html", info=info, formats=formats, error=error)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    format_id = request.form.get('format_id')
    if not url or not format_id:
        return redirect(url_for('index'))

    tmpdir = tempfile.mkdtemp()
    ydl_opts = get_ydl_opts(format_id=format_id, download=True, tmpdir=tmpdir)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e:
        shutil.rmtree(tmpdir)
        return f"Download failed: {e}", 500

    # Send file
    response = send_file(
        filename,
        as_attachment=True,
        download_name=os.path.basename(filename)
    )

    @response.call_on_close
    def cleanup():
        shutil.rmtree(tmpdir)

    return response

if __name__ == "__main__":
    if not os.path.exists(COOKIE_FILE):
        print("❌ cookies.txt NOT FOUND!")
    else:
        print("✅ cookies.txt FOUND:", os.path.abspath(COOKIE_FILE))

    print("Cookies file:", os.path.abspath(COOKIE_FILE))
    app.run(host="0.0.0.0", port=8000, debug=True)
