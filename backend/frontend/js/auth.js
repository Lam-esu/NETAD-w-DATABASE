document.addEventListener("DOMContentLoaded", function () {
    const cachedRole = sessionStorage.getItem("userRole");

    if (cachedRole) {
        applyRole(cachedRole);
        setupLogout();
        return;
    }

    checkSessionFromServer();
});

async function checkSessionFromServer() {
    try {
        const response = await fetch("/api/auth/me", {
            method: "GET",
            credentials: "include"
        });

        if (!response.ok) {
            console.warn("No valid session. Redirecting to login.");
            window.location.href = "/";
            return;
        }

        const user = await response.json();

        const role = String(user.role).trim().toLowerCase();

        sessionStorage.setItem("userRole", role);
        sessionStorage.setItem("username", user.username);

        applyRole(role);
        setupLogout();

    } catch (error) {
        console.error("Auth check failed:", error);
        window.location.href = "/";
    }
}

function applyRole(role) {
    role = String(role).trim().toLowerCase();

    document.querySelectorAll(".admin-only").forEach(item => {
        if (role === "admin") {
            item.style.display = "block";
        } else {
            item.remove();
        }
    });

    const page = window.location.pathname;

    if (
        role !== "admin" &&
        (
            page.includes("logs.html") ||
            page.includes("admin.html")
        )
    ) {
        window.location.href = "/dashboard.html";
        return;
    }

    document.querySelectorAll(".sidebar a").forEach(link => {
        link.classList.remove("active");

        const href = link.getAttribute("href");

        if (href && page.includes(href)) {
            link.classList.add("active");
        }
    });
}

function setupLogout() {
    const logoutBtn = document.getElementById("logoutBtn");

    if (!logoutBtn) return;

    logoutBtn.addEventListener("click", async function () {
        sessionStorage.clear();

        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                credentials: "include"
            });
        } catch (error) {
            console.error("Logout error:", error);
        }

        window.location.href = "/";
    });
}