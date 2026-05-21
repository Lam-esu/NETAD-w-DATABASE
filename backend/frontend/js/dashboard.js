const API_BASE = "http://127.0.0.1:8000";

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "/";
            return;
        }

        const user = await response.json();
        console.log("Logged in as:", user.username);

    } catch (error) {
        console.error(error);
        window.location.href = "/";
    }
}

async function logout() {
    await fetch(`${API_BASE}/api/auth/logout`, {
        method: "POST",
        credentials: "include"
    });

    localStorage.clear();
    window.location.href = "/";
}

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
}

checkAuth();