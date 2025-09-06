from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading

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


# ✅ Clean cookies before use
def clean_cookies(cookies_path):
    """Remove invalid/garbled cookie lines (Railway में error रोकने के लिए)"""
    try:
        if os.path.exists(cookies_path):
            cleaned_lines = []
            with open(cookies_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip() and not line.startswith(".smartadserver.com"):
                        cleaned_lines.append(line)
            with open(cookies_path, "w", encoding="utf-8") as f:
                f.writelines(cleaned_lines)
            print("✅ Cookies cleaned successfully")
    except Exception as e:
        print(f"⚠️ Cookie cleanup failed: {e}")


def download_worker(url, filetype, quality, filename):
    """Worker thread for downloading video/audio"""
    global progress_data
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        'progress_hooks': [progress_hook],
        'outtmpl': filepath,
    }

    # ✅ Add cookies (Railway env var OR local file)
    cookies_env = os.environ.get("COOKIES")
    cookies_path = os.path.join(os.getcwd(), "cookies.txt")

    if cookies_env:
        with open(cookies_path, "w") as f:
            f.write(cookies_env)
        clean_cookies(cookies_path)   # ✅ Clean after writing
        ydl_opts["cookiefile"] = cookies_path
    elif os.path.exists(cookies_path):
        clean_cookies(cookies_path)   # ✅ Clean local file
        ydl_opts["cookiefile"] = cookies_path

    if filetype == "mp4":
        if quality == "highest":
            ydl_opts['format'] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"
        else:
            ydl_opts['format'] = f"bestvideo[height<={quality.replace('p','')}][ext=mp4]+bestaudio[ext=m4a]/best"
        ydl_opts['merge_output_format'] = "mp4"
    else:
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
        if quality == "2160p" or quality == "4k":
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

    # ✅ Add cookies (Railway env var OR local file)
    cookies_env = os.environ.get("COOKIES")
    cookies_path = os.path.join(os.getcwd(), "cookies.txt")

    ydl_opts = {'quiet': True}
    if cookies_env:
        with open(cookies_path, "w") as f:
            f.write(cookies_env)
        clean_cookies(cookies_path)   # ✅ Clean before use
        ydl_opts["cookiefile"] = cookies_path
    elif os.path.exists(cookies_path):
        clean_cookies(cookies_path)   # ✅ Clean before use
        ydl_opts["cookiefile"] = cookies_path

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway ke liye
    app.run(host="0.0.0.0", port=port)
