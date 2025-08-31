from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Temporary download folder
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Store last downloaded file paths
last_files = {}

@app.route("/")
def index():
    return render_template("index.html")

# ✅ Thumbnail endpoint
@app.route("/thumbnail", methods=["POST"])
def thumbnail():
    data = request.get_json()
    url = data.get("url")
    try:
        with yt_dlp.YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "thumbnail": info.get("thumbnail"),
                "title": info.get("title")
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ✅ Download video
@app.route("/download", methods=["POST"])
def download():
    try:
        url = request.form["url"]
        file_type = request.form["type"]
        quality = request.form["quality"]

        unique_id = str(uuid.uuid4())
        outtmpl = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

        ydl_opts = {
            "outtmpl": outtmpl,
            "format": f"bestvideo[height<={quality.replace('p','')}]+bestaudio/best"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        last_files[unique_id] = file_path
        return jsonify({"status": "success", "file_id": unique_id})

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# ✅ Serve file to user
@app.route("/get_file/<file_id>")
def get_file(file_id):
    try:
        if file_id in last_files:
            file_path = last_files[file_id]
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
        return jsonify({"status": "error", "error": "File not found!"}), 404
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ✅ Run on Railway dynamic port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
