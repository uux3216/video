from flask import Flask, request, render_template, send_file, redirect, url_for
import yt_dlp
import os
import tempfile
import shutil

app = Flask(__name__)

# Path to your cookies file (update if needed)
COOKIE_FILE = "cookies.txt"

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
                ydl_opts = get_ydl_opts()
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                # Filter progressive mp4 formats (video + audio)
                for f in info.get('formats', []):
                    if (f.get('ext') == 'mp4' and
                        f.get('acodec') != 'none' and
                        f.get('vcodec') != 'none'):
                        formats.append({
                            "format_id": f["format_id"],
                            "resolution": f.get("height", "N/A"),
                            "filesize": round((f.get("filesize") or f.get("filesize_approx") or 0) / (1024*1024), 2)
                        })

                if not formats:
                    error = "No progressive mp4 formats available for this video."

            except Exception as e:
                error = f"Error fetching video info: {e}"

    return render_template("index.html", info=info, formats=formats, error=error)


@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    format_id = request.form.get('format_id')
    if not url or not format_id:
        return redirect(url_for('index'))

    # Create a temp directory for download
    tmpdir = tempfile.mkdtemp()
    ydl_opts = get_ydl_opts(format_id=format_id, download=True, tmpdir=tmpdir)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e:
        shutil.rmtree(tmpdir)  # clean up temp dir on error
        return f"Download failed: {e}", 500

    # Send file to user and cleanup temp after response is done
    response = send_file(
        filename,
        as_attachment=True,
        download_name=os.path.basename(filename)
    )
    
    # Cleanup temp directory after request is complete
    @response.call_on_close
    def cleanup():
        shutil.rmtree(tmpdir)

    return response


if __name__ == "__main__":
    print(f"Make sure your cookies file is here: {os.path.abspath(COOKIE_FILE)}")
    app.run(host="0.0.0.0", port=8000, debug=True)

