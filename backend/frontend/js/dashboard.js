document.addEventListener("DOMContentLoaded", function () {
    loadDashboardStats();
});

async function loadDashboardStats() {
    try {
        const response = await fetch("/api/dashboard/stats", {
            method: "GET",
            credentials: "include"
        });

        if (!response.ok) {
            console.warn("Dashboard stats failed:", response.status);
            return;
        }

        const data = await response.json();

        const devicesCount = document.getElementById("devicesCount");
        const cameraStatus = document.getElementById("cameraStatus");
        const activeUsers = document.getElementById("activeUsers");
        const logsToday = document.getElementById("logsToday");

        if (devicesCount) {
            devicesCount.textContent = data.devices ?? 0;
        }

        if (cameraStatus) {
            cameraStatus.textContent = data.camera_status ?? "UNAVAILABLE";
        }

        if (activeUsers) {
            activeUsers.textContent = data.active_users ?? 0;
        }

        if (logsToday) {
            logsToday.textContent = data.total_logs ?? 0;
        }

    } catch (error) {
        console.error("Dashboard stats error:", error);
    }
}