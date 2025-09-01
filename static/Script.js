const urlInput = document.getElementById("videoURL");
const preview = document.getElementById("preview");
const thumbnailImg = document.getElementById("videoThumbnail");
const videoTitle = document.getElementById("videoTitle");

// URL paste hone par thumbnail fetch
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

            // ✅ Scroll smoothly to the preview section
            preview.scrollIntoView({ behavior: "smooth", block: "start" });
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

    let interval;

    try {
        // Start polling progress
        interval = setInterval(async () => {
            const res = await fetch("/progress");
            const data = await res.json();

            progressBar.style.width = data.progress + "%";

            if (data.progress < 50) {
                progressBar.style.background = "orange";
            } else if (data.progress < 100) {
                progressBar.style.background = "yellowgreen";
            } else {
                progressBar.style.background = "limegreen";
            }

            if (data.progress >= 100 && data.status === "finished") {
                clearInterval(interval);
                const resp = await fetch("/get_file");
                if (resp.ok) {
                    const blob = await resp.blob();
                    const link = document.createElement("a");
                    link.href = window.URL.createObjectURL(blob);

                    // backend se filename bhejna zaroori hai
                    const disposition = resp.headers.get("Content-Disposition");
                    let fileName = "downloaded_file";
                    if (disposition && disposition.includes("filename=")) {
                        fileName = disposition.split("filename=")[1].replace(/['"]/g, "");
                    }

                    link.download = fileName;
                    link.click();
                } else {
                    alert("⚠️ File not found on server!");
                }
            }

            if (data.status === "error") {
                clearInterval(interval);
                alert("⚠️ Error: " + (data.error || "Something went wrong!"));
            }
        }, 1000);

        // Start download request
        const resp = await fetch("/download", { method: "POST", body: formData });
        if (!resp.ok) {
            clearInterval(interval);
            alert("⚠️ Failed to start download!");
        }
    } catch (err) {
        clearInterval(interval);
        console.error("Download error:", err);
        alert("⚠️ Something went wrong while downloading!");
    }
});
