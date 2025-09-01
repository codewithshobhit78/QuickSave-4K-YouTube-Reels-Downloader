web: bash -c "apt-get update && apt-get install -y ffmpeg && gunicorn -w 2 -k gthread --threads 8 --timeout 120 app:app"
