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

@app.route("/download", methods=["POST"])
def download():
    try:
        url = request.form["url"]
        file_type = request.form["type"]
        quality = request.form["quality"]

        # Unique filename (to avoid overwriting)
        unique_id = str(uuid.uuid4())
        outtmpl = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

        # ydl options
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestvideo[height<=" + quality.replace("p", "") + "]+bestaudio/best"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # Save file path in memory with unique_id
        last_files[unique_id] = file_path

        return jsonify({"status": "success", "file_id": unique_id})

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/get_file/<file_id>")
def get_file(file_id):
    try:
        if file_id in last_files:
            file_path = last_files[file_id]
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
        return jsonify({"status": "error", "error": "File not found on server!"}), 404
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
