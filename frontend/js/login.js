document.addEventListener("DOMContentLoaded", function () {
    console.log("login.js loaded");

    const loginForm = document.getElementById("loginForm");
    const message = document.getElementById("message");

    if (!loginForm) {
        console.error("loginForm not found");
        return;
    }

    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        console.log("Login button clicked");

        const username = document.getElementById("username").value;
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

            console.log("Login response status:", response.status);

            const data = await response.json();
            console.log("Login response data:", data);

            if (response.ok) {
                message.textContent = "Login successful. Redirecting...";
                window.location.assign("/dashboard.html");
            } else {
                message.textContent = data.error || "Login failed";
            }

        } catch (error) {
            console.error("Login error:", error);
            message.textContent = "Server error. Check Flask terminal.";
        }
    });
});