const urlInput = document.getElementById("videoURL");
const preview = document.getElementById("preview");
const thumbnailImg = document.getElementById("videoThumbnail");
const videoTitle = document.getElementById("videoTitle");

urlInput.addEventListener("change", async function () {
    const url = urlInput.value.trim();
    if (!url) return;

    try {
        const res = await fetch("/thumbnail", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });
        const data = await res.json();

        if (data.thumbnail) {
            thumbnailImg.src = data.thumbnail;
            videoTitle.textContent = data.title;
            preview.style.display = "block";
        }
    } catch (err) {
        console.error("Thumbnail fetch error:", err);
        alert("⚠️ Failed to load video info!");
    }
});

document.getElementById("downloadForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const progressBar = document.getElementById("progressBar");
    progressBar.style.width = "0%";
    progressBar.style.background = "orange";

    try {
        const resp = await fetch("/download", { method: "POST", body: formData });
        const data = await resp.json();

        if (data.status === "success") {
            const file_id = data.file_id;
            const fileResp = await fetch(`/get_file/${file_id}`);
            if (fileResp.ok) {
                const blob = await fileResp.blob();
                const link = document.createElement("a");
                link.href = window.URL.createObjectURL(blob);

                // Extract filename from response headers
                const disposition = fileResp.headers.get("Content-Disposition");
                let fileName = "downloaded_file";
                if (disposition && disposition.includes("filename=")) {
                    fileName = disposition.split("filename=")[1].replace(/['"]/g, "");
                }

                link.download = fileName;
                link.click();
            } else {
                alert("⚠️ File not found on server!");
            }
        } else {
            alert("⚠️ Download failed: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        console.error("Download error:", err);
        alert("⚠️ Something went wrong while downloading!");
    }
});
