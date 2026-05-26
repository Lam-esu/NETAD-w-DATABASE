document.addEventListener("DOMContentLoaded", async function () {
    const secretBox = document.getElementById("secretBox");
    const form = document.getElementById("setupTwoFactorForm");
    const enableBtn = document.getElementById("enable2faBtn");

    if (!secretBox || !form) {
        console.error("Required 2FA setup elements not found.");
        alert("2FA page error. Missing form elements.");
        return;
    }

    try {
        const response = await fetch("/api/auth/2fa/first-setup", {
            method: "POST",
            credentials: "include"
        });

        const data = await response.json();

        console.log("2FA SETUP RESPONSE:", data);

        if (!response.ok) {
            alert(data.error || "Unable to start 2FA setup.");
            window.location.href = "/";
            return;
        }

        secretBox.textContent = data.secret;

    } catch (error) {
        console.error("2FA setup error:", error);
        alert("Server error while setting up 2FA.");
        window.location.href = "/";
        return;
    }

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const codeInput = document.getElementById("code");
        const code = codeInput.value.trim();

        if (!/^\d{6}$/.test(code)) {
            alert("Please enter a valid 6-digit code.");
            return;
        }

        if (enableBtn) {
            enableBtn.disabled = true;
            enableBtn.textContent = "Verifying...";
        }

        try {
            const response = await fetch("/api/auth/2fa/first-enable", {
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

            console.log("2FA ENABLE RESPONSE:", data);

            if (response.ok) {
                const role = String(data.user.role).trim().toLowerCase();

                sessionStorage.setItem("userRole", role);
                sessionStorage.setItem("username", data.user.username);

                alert("2FA enabled successfully.");
                window.location.href = "/dashboard.html";
                return;
            }

            alert(data.error || "Invalid 2FA code.");

        } catch (error) {
            console.error("2FA enable error:", error);
            alert("Server error while enabling 2FA.");
        } finally {
            if (enableBtn) {
                enableBtn.disabled = false;
                enableBtn.textContent = "Enable 2FA";
            }
        }
    });
});