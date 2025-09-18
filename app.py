from flask import Flask, request, render_template, send_file, redirect, url_for
import yt_dlp
import os
import tempfile

app = Flask(__name__)

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
                with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                # filter formats (progressive mp4)
                for f in info.get('formats', []):
                    if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        formats.append({
                            "format_id": f["format_id"],
                            "resolution": f.get("height"),
                            "filesize": round((f.get("filesize") or f.get("filesize_approx") or 0)/(1024*1024), 2)
                        })
            except Exception as e:
                error = f"Error fetching video info: {e}"

    return render_template("index.html", info=info, formats=formats, error=error)


@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    format_id = request.form.get('format_id')
    if not url or not format_id:
        return redirect(url_for('index'))

    # create temp file
    tmpdir = tempfile.mkdtemp()
    # to save file in temp
    ydl_opts = {
        "format": format_id,
        "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e:
        return f"Download failed: {e}", 500

    # send file to user
    return send_file(
        filename, 
        as_attachment=True,
        download_name=os.path.basename(filename)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
