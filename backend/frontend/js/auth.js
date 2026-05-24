window.addEventListener("load", async function () {
    const cachedRole = sessionStorage.getItem("userRole");

    if (cachedRole) {
        applyRole(cachedRole);
        setupLogout();
        return;
    }

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
        console.error(error);
        window.location.href = "/";
    }
});

function applyRole(role) {
    if (role !== "admin") {
        document.querySelectorAll(".admin-only").forEach(item => {
            item.style.display = "none";
        });

        const page = window.location.pathname;

        if (page.includes("logs.html") || page.includes("admin.html")) {
            alert("Admin access only");
            window.location.href = "/dashboard.html";
        }
    }

    document.querySelectorAll(".sidebar a").forEach(link => {
        link.classList.remove("active");

        if (window.location.pathname.includes(link.getAttribute("href"))) {
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