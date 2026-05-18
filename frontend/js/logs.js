document.addEventListener("DOMContentLoaded", function () {
    loadLogs();

    const searchBtn = document.getElementById("searchBtn");
    const clearSearchBtn = document.getElementById("clearSearchBtn");
    const exportBtn = document.getElementById("exportLogs");

    searchBtn.addEventListener("click", function () {
        loadLogs();
    });

    clearSearchBtn.addEventListener("click", function () {
        document.getElementById("searchUsername").value = "";
        document.getElementById("searchAction").value = "";
        loadLogs();
    });

    exportBtn.addEventListener("click", function () {
        window.location.href = "/api/logs/export";
    });

    document.getElementById("searchUsername").addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            loadLogs();
        }
    });

    document.getElementById("searchAction").addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            loadLogs();
        }
    });
});

async function loadLogs() {
    const username = document.getElementById("searchUsername").value.trim();
    const action = document.getElementById("searchAction").value.trim();
    const logsTable = document.getElementById("logsTable");

    const params = new URLSearchParams();

    if (username) {
        params.append("username", username);
    }

    if (action) {
        params.append("action", action);
    }

    let url = "/api/logs";

    if (params.toString()) {
        url += "?" + params.toString();
    }

    try {
        logsTable.innerHTML = `
            <tr>
                <td colspan="4">Loading logs...</td>
            </tr>
        `;

        const response = await fetch(url, {
            method: "GET",
            credentials: "include"
        });

        if (!response.ok) {
            logsTable.innerHTML = `
                <tr>
                    <td colspan="4">Admin access required or failed to load logs</td>
                </tr>
            `;
            return;
        }

        const logs = await response.json();

        logsTable.innerHTML = "";

        if (logs.length === 0) {
            logsTable.innerHTML = `
                <tr>
                    <td colspan="4">No logs found</td>
                </tr>
            `;
            return;
        }

        logs.forEach(log => {
            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${escapeHTML(log.username)}</td>
                <td>${escapeHTML(log.action)}</td>
                <td>${escapeHTML(log.ip_address)}</td>
                <td>${escapeHTML(log.created_at)}</td>
            `;

            logsTable.appendChild(row);
        });

    } catch (error) {
        console.error("Logs error:", error);

        logsTable.innerHTML = `
            <tr>
                <td colspan="4">Server error while loading logs</td>
            </tr>
        `;
    }
}

function escapeHTML(value) {
    if (!value) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}