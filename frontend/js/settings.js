const API_BASE = "http://127.0.0.1:8000";

async function checkAuth() {
    const response = await fetch(`${API_BASE}/api/auth/me`, {
        credentials: "include"
    });

    if (!response.ok) {
        window.location.href = "index.html";
    }
}

const saveSettingsBtn = document.getElementById("saveSettingsBtn");

if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener("click", async () => {
        const select = document.querySelector("select");
        const autoLogout = select.value;

        const response = await fetch(`${API_BASE}/api/settings/save`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({ auto_logout: autoLogout })
        });

        const result = await response.json();
        alert(result.message || result.error);
    });
}

checkAuth();