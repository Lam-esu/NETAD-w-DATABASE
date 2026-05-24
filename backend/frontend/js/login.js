document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");

    if (!loginForm) {
        console.error("loginForm not found");
        return;
    }

    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;

        try {
            const response = await fetch("/api/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            console.log("LOGIN RESPONSE:", data);

            if (response.ok) {
                const role = String(data.user.role).trim().toLowerCase();

                sessionStorage.setItem("userRole", role);
                sessionStorage.setItem("username", data.user.username);

                window.location.href = "/dashboard.html";
            } else {
                alert(data.error || "Login failed");
            }

        } catch (error) {
            console.error("Login error:", error);
            alert("Server error. Check Railway logs.");
        }
    });
});