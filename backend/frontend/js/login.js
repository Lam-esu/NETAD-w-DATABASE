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

            let data = {};

            try {
                data = await response.json();
            } catch (jsonError) {
                console.error("Invalid JSON response:", jsonError);
                alert("Server returned an invalid response.");
                return;
            }

            console.log("LOGIN RESPONSE:", data);

            if (response.ok) {
                if (data.requires_2fa === true) {
                    window.location.href = "/verify-2fa.html";
                    return;
                }

                if (!data.user) {
                    alert("Login response missing user data.");
                    return;
                }

                const role = String(data.user.role).trim().toLowerCase();

                sessionStorage.setItem("userRole", role);
                sessionStorage.setItem("username", data.user.username);

                window.location.href = "/dashboard.html";
                return;
            }

            alert(data.error || "Login failed");

        } catch (error) {
            console.error("Login error:", error);
            alert("Server error. Check Railway logs.");
        }
    });
});