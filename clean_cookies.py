# clean_cookies.py
def clean_cookies(input_file, output_file):
    """
    Removes invalid/extra cookies and keeps only YouTube + Google cookies.
    Format stays Netscape compatible for yt-dlp.
    """
    try:
        with open(input_file, "r", encoding="utf-8") as infile:
            lines = infile.readlines()

        clean_lines = []
        for line in lines:
            # comment या खाली लाइन रहने दो
            if line.strip().startswith("#") or not line.strip():
                clean_lines.append(line)
                continue

            # सिर्फ youtube और google domains रहने दो
            if "youtube.com" in line or "google.com" in line:
                clean_lines.append(line)

        with open(output_file, "w", encoding="utf-8") as outfile:
            outfile.writelines(clean_lines)

        print("✅ Cookies cleaned successfully")

    except Exception as e:
        print(f"⚠️ Cookie cleaning failed: {e}")
