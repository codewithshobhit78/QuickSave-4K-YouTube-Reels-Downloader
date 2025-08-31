document.getElementById("downloadBtn").addEventListener("click", async () => {
    const url = document.getElementById("url").value.trim();
    const format = document.getElementById("format").value;
    const quality = document.getElementById("quality").value;

    if (!url) {
        alert("Please enter a valid URL.");
        return;
    }

    // Disable button and show loading text
    const btn = document.getElementById("downloadBtn");
    btn.disabled = true;
    btn.innerText = "Downloading...";

    try {
        const response = await fetch("/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url, format, quality })
        });

        if (!response.ok) {
            throw new Error("Server error: " + response.statusText);
        }

        // File download
        const blob = await response.blob();
        const disposition = response.headers.get("Content-Disposition");
        let filename = "video.mp4";

        if (disposition && disposition.includes("filename=")) {
            filename = disposition.split("filename=")[1].replace(/"/g, "");
        }

        const link = document.createElement("a");
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

    } catch (error) {
        console.error(error);
        alert("❌ Download failed: " + error.message);
    }

    // Reset button
    btn.disabled = false;
    btn.innerText = "Download";
});
