const API_BASE = "http://127.0.0.1:8000";

async function checkAuth() {
    const response = await fetch(`${API_BASE}/api/auth/me`, {
        credentials: "include"
    });

    if (!response.ok) {
        window.location.href = "index.html";
    }
}

function loadCameraStream() {
    const cameraImage = document.querySelector(".single-camera-card img");

    if (cameraImage) {
        cameraImage.src = `${API_BASE}/api/camera/stream?t=${Date.now()}`;
    }
}

const refreshCamera = document.getElementById("refreshCamera");
const snapshotBtn = document.getElementById("snapshotBtn");
const fullscreenBtn = document.getElementById("fullscreenBtn");

if (refreshCamera) {
    refreshCamera.addEventListener("click", () => {
        loadCameraStream();
        alert("Camera feed refreshed.");
    });
}

if (snapshotBtn) {
    snapshotBtn.addEventListener("click", () => {
        alert("Snapshot button clicked. Backend snapshot storage can be added next.");
    });
}

if (fullscreenBtn) {
    fullscreenBtn.addEventListener("click", () => {
        const cameraImage = document.querySelector(".single-camera-card img");

        if (cameraImage && cameraImage.requestFullscreen) {
            cameraImage.requestFullscreen();
        }
    });
}

checkAuth();
loadCameraStream();