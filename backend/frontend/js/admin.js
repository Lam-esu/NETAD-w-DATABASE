document.addEventListener("DOMContentLoaded", function () {

    loadUsers();

    const addUserBtn = document.getElementById("addUserBtn");

    if (addUserBtn) {
        addUserBtn.addEventListener("click", addUser);
    }

});

async function loadUsers() {

    const usersTable = document.getElementById("usersTable");

    try {

        const response = await fetch("/api/users", {
            method: "GET",
            credentials: "include"
        });

        if (!response.ok) {

            usersTable.innerHTML = `
                <tr>
                    <td colspan="5">
                        Admin access required
                    </td>
                </tr>
            `;

            return;
        }

        const users = await response.json();

        usersTable.innerHTML = "";

        if (users.length === 0) {

            usersTable.innerHTML = `
                <tr>
                    <td colspan="5">
                        No users found
                    </td>
                </tr>
            `;

            return;
        }

        users.forEach(user => {

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${escapeHTML(user.username)}</td>

                <td>${escapeHTML(user.email)}</td>

                <td>${escapeHTML(user.role)}</td>

                <td>
                    ${user.is_active ? "Active" : "Disabled"}
                </td>

                <td>
                    <div class="user-actions">

                        <button onclick="resetPassword(${user.id})">
                            Reset Password
                        </button>

                        <button
                            class="danger-btn"
                            onclick="deleteUser(${user.id}, '${escapeHTML(user.username)}')"
                        >
                            Remove
                        </button>

                    </div>
                </td>
            `;

            usersTable.appendChild(row);

        });

    } catch (error) {

        console.error("Failed to load users:", error);

        usersTable.innerHTML = `
            <tr>
                <td colspan="5">
                    Failed to load users
                </td>
            </tr>
        `;
    }
}

async function addUser() {

    const username = document.getElementById("newUsername").value.trim();

    const email = document.getElementById("newEmail").value.trim();

    const password = document.getElementById("newPassword").value;

    const role = document.getElementById("newRole").value.trim().toLowerCase();

    if (!username || !email || !password) {
        alert("Please fill in all fields");
        return;
    }

    try {

        const response = await fetch("/api/auth/register", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            credentials: "include",

            body: JSON.stringify({
                username,
                email,
                password,
                role
            })
        });

        const data = await response.json();

        if (response.ok) {

            alert("User added successfully");

            document.getElementById("newUsername").value = "";
            document.getElementById("newEmail").value = "";
            document.getElementById("newPassword").value = "";

            loadUsers();

        } else {

            alert(data.error || "Failed to add user");

        }

    } catch (error) {

        console.error("Add user error:", error);

        alert("Server error");

    }
}

async function deleteUser(userId, username) {

    const confirmDelete = confirm(
        `Are you sure you want to remove "${username}"?`
    );

    if (!confirmDelete) return;

    try {

        const response = await fetch(
            `/api/users/${userId}/delete`,
            {
                method: "DELETE",
                credentials: "include"
            }
        );

        const data = await response.json();

        if (response.ok) {

            alert("User removed successfully");

            loadUsers();

        } else {

            alert(data.error || "Failed to remove user");

        }

    } catch (error) {

        console.error("Delete user error:", error);

        alert("Server error");

    }
}

async function resetPassword(userId) {

    const newPassword = prompt(
        "Enter new password (minimum 8 characters):"
    );

    if (!newPassword) return;

    try {

        const response = await fetch(
            `/api/users/${userId}/reset-password`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                credentials: "include",

                body: JSON.stringify({
                    password: newPassword
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            alert("Password reset successfully");

        } else {

            alert(data.error || "Failed to reset password");

        }

    } catch (error) {

        console.error("Reset password error:", error);

        alert("Server error");

    }
}

function escapeHTML(value) {

    if (!value) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}