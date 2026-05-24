document.addEventListener("DOMContentLoaded", function () {
    const role = sessionStorage.getItem("userRole");

    if (!role) {
        checkSessionFromServer();
        return;
    }

    applyRole(role);
    setupLogout();
});

async function checkSessionFromServer() {
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

        sessionStorage.setItem("userRole", user.role);
        sessionStorage.setItem("username", user.username);

        applyRole(user.role);
        setupLogout();

    } catch (error) {
        console.error("Auth check failed:", error);
        window.location.href = "/";
    }
}

function applyRole(role) {
    const adminItems = document.querySelectorAll(".admin-only");

    adminItems.forEach(item => {
        if (role === "admin") {
            item.style.display = "block";
        } else {
            item.remove();
        }
    });

    const page = window.location.pathname;

    if (
        role !== "admin" &&
        (page.includes("logs.html") || page.includes("admin.html"))
    ) {
        window.location.href = "/dashboard.html";
        return;
    }

    document.querySelectorAll(".sidebar a").forEach(link => {
        link.classList.remove("active");

        const href = link.getAttribute("href");

        if (page.includes(href)) {
            link.classList.add("active");
        }
    });
}

function setupLogout() {
    const logoutBtn = document.getElementById("logoutBtn");

    if (!logoutBtn) return;

    logoutBtn.addEventListener("click", async function () {
        sessionStorage.clear();

        await fetch("/api/auth/logout", {
            method: "POST",
            credentials: "include"
        });

        window.location.href = "/";
    });
}