const urlInput = document.getElementById("videoURL");
const preview = document.getElementById("preview");
const thumbnailImg = document.getElementById("videoThumbnail");
const videoTitle = document.getElementById("videoTitle");

// ✅ Jaise hi user URL paste kare → thumbnail fetch ho jaye
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
    }
});

document.getElementById("downloadForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const formData = new FormData(this);

    // Reset progress bar
    const progressBar = document.getElementById("progressBar");
    progressBar.style.width = "0%";
    progressBar.style.background = "orange";

    // Start progress polling
    const interval = setInterval(async () => {
        const res = await fetch("/progress");
        const data = await res.json();

        // update bar
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

                const fileType = document.querySelector("select[name='type']").value;
                link.download = (fileType === "mp3") ? "audio.mp3" : "video.mp4";
                link.click();
            }
        }

        if (data.status === "error") {
            clearInterval(interval);
            alert("⚠️ Error: " + (data.error || "Something went wrong!"));
        }
    }, 1000);

    await fetch("/download", {
        method: "POST",
        body: formData
    });
});
