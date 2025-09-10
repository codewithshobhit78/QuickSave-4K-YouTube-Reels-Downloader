from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading
import clean_cookies   # ✅ new import

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ✅ Global progress
progress_data = {"progress": 0, "file": None, "status": "idle"}


def progress_hook(d):
    global progress_data
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').replace('%', '')
        try:
            progress_data["progress"] = float(percent)
            progress_data["status"] = "downloading"
        except:
            progress_data["progress"] = 0
    elif d['status'] == 'finished':
        progress_data["progress"] = 100
        progress_data["status"] = "finished"


def download_worker(url, filetype, quality, filename):
    """Worker thread for downloading video/audio"""
    global progress_data
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        'progress_hooks': [progress_hook],
        'outtmpl': filepath,
    }

    # ✅ Auto clean cookies (Railway env var OR local file)
    cookies_env = os.environ.get("COOKIES")
    cookies_path = os.path.join(os.getcwd(), "cookies.txt")
    clean_path = os.path.join(os.getcwd(), "cookies_clean.txt")

    if cookies_env:
        with open(cookies_path, "w", encoding="utf-8") as f:
            f.write(cookies_env)
        clean_cookies.clean_cookies(cookies_path, clean_path)
        ydl_opts["cookiefile"] = clean_path
    elif os.path.exists(cookies_path):
        clean_cookies.clean_cookies(cookies_path, clean_path)
        ydl_opts["cookiefile"] = clean_path

    # ✅ Video/audio format logic (fixed for 1080p/4K)
    if filetype == "mp4":
        # Use adaptive streams, auto fallback, merge to mp4
        if quality.lower() in ["highest", "1080p", "720p", "480p", "360p"]:
            ydl_opts['format'] = (
                f"(bestvideo[height<={quality.replace('p','')}]+bestaudio)/bestvideo+bestaudio/best"
            )
        else:
            ydl_opts['format'] = "bestvideo+bestaudio/best"
        ydl_opts['merge_output_format'] = "mp4"
    else:
        # audio only
        ydl_opts['format'] = "bestaudio[ext=m4a]/bestaudio"
        ydl_opts['merge_output_format'] = "mp3"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # find actual downloaded file
        downloaded_file = None
        for file in os.listdir(DOWNLOAD_DIR):
            if filename.split(".")[0] in file:
                downloaded_file = os.path.join(DOWNLOAD_DIR, file)
                break

        progress_data["file"] = downloaded_file

    except Exception as e:
        progress_data["status"] = "error"

        # ✅ 4K-specific error message
        if quality.lower() in ["2160p", "4k"]:
            progress_data["error"] = "4K download failed, try 1080p or highest available!"
        else:
            progress_data["error"] = str(e)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/download', methods=['POST'])
def download():
    global progress_data
    url = request.form.get("url")
    filetype = request.form.get("type", "mp4")
    quality = request.form.get("quality", "highest")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # reset progress
    progress_data = {"progress": 0, "file": None, "status": "starting"}

    # unique filename
    filename = str(uuid.uuid4()) + ".%(ext)s"

    # background thread
    t = threading.Thread(target=download_worker, args=(url, filetype, quality, filename))
    t.start()

    return jsonify({"message": "Download started"})


@app.route('/progress')
def progress():
    return jsonify(progress_data)


@app.route('/get_file')
def get_file():
    if progress_data.get("file") and os.path.exists(progress_data["file"]):
        # ✅ Cleanup logic added here
        filepath = progress_data["file"]
        response = send_file(filepath, as_attachment=True)
        try:
            os.remove(filepath)  # Delete after sending
            print(f"✅ Deleted temp file: {filepath}")
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
        return response
    return jsonify({"error": "File not ready"}), 404


@app.route('/thumbnail', methods=['POST'])
def thumbnail():
    url = request.json.get("url")

    # ✅ Auto clean cookies for thumbnail too
    cookies_env = os.environ.get("COOKIES")
    cookies_path = os.path.join(os.getcwd(), "cookies.txt")
    clean_path = os.path.join(os.getcwd(), "cookies_clean.txt")

    ydl_opts = {'quiet': True}
    if cookies_env:
        with open(cookies_path, "w", encoding="utf-8") as f:
            f.write(cookies_env)
        clean_cookies.clean_cookies(cookies_path, clean_path)
        ydl_opts["cookiefile"] = clean_path
    elif os.path.exists(cookies_path):
        clean_cookies.clean_cookies(cookies_path, clean_path)
        ydl_opts["cookiefile"] = clean_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "thumbnail": info.get("thumbnail", ""),
                "title": info.get("title", "Video")
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ✅ Added Privacy Policy page
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# ✅ Added Terms & Conditions page
@app.route("/terms")
def terms():
    return render_template("terms.html")

# ✅ Added Disclaimer page
@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway ke liye
    app.run(host="0.0.0.0", port=port)
