web: bash -c "which ffmpeg || (apt-get update && apt-get install -y ffmpeg) && gunicorn -w 2 -k gthread --threads 8 --timeout 180 app:app"
