document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("twoFactorForm");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const code = document.getElementById("code").value.trim();

        try {
            const response = await fetch("/api/auth/verify-2fa", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify({
                    code: code
                })
            });

            const data = await response.json();

            if (response.ok) {
                const role = String(data.user.role).trim().toLowerCase();

                sessionStorage.setItem("userRole", role);
                sessionStorage.setItem("username", data.user.username);

                window.location.href = "/dashboard.html";
            } else {
                alert(data.error || "Invalid 2FA code");
            }

        } catch (error) {
            console.error(error);
            alert("Server error while verifying 2FA");
        }
    });
});