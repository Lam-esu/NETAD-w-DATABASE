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

        if (!username || !password) {
            alert("Please enter your username and password.");
            return;
        }

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
                /*
                    If 2FA is enabled for this account,
                    redirect first to the 2FA verification page.
                */
                if (data.requires_2fa) {
                    window.location.href = "/verify-2fa.html";
                    return;
                }

                /*
                    Normal login without 2FA.
                    Store role locally for faster sidebar loading.
                */
                const role = String(data.user.role).trim().toLowerCase();

                sessionStorage.setItem("userRole", role);
                sessionStorage.setItem("username", data.user.username);

                window.location.href = "/dashboard.html";
                return;
            }

            alert(data.error || "Login failed");

        } catch (error) {
            console.error("Login error:", error);
            alert("Server error. Check Railway or Flask terminal.");
        }
    });
});