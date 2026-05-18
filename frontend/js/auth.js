document.addEventListener("DOMContentLoaded", async function () {
    try {
        const response = await fetch("/api/auth/me", {
            method: "GET",
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "/";
            return;
        }

        const user = await response.json();
        console.log("Logged in as:", user.username);

    } catch (error) {
        console.error("Auth check failed:", error);
        window.location.href = "/";
    }

    const logoutBtn = document.getElementById("logoutBtn");

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async function () {
            await fetch("/api/auth/logout", {
                method: "POST",
                credentials: "include"
            });

            window.location.href = "/dashboard.html";
        });
    }
});