document.addEventListener("DOMContentLoaded", function () {

    const loginForm =
    document.getElementById(
        "loginForm"
    );

    if (!loginForm) return;

    loginForm.addEventListener(
        "submit",

        async function (e) {

            e.preventDefault();

            const username =
            document.getElementById(
                "username"
            ).value.trim();

            const password =
            document.getElementById(
                "password"
            ).value;

            try {

                const response =
                await fetch(

                    "/api/auth/login",

                    {
                        method:
                        "POST",

                        headers: {
                            "Content-Type":
                            "application/json"
                        },

                        credentials:
                        "include",

                        body:
                        JSON.stringify({

                            username,
                            password

                        })

                    }

                );

                const data =
                await response.json();

                if (
                    response.ok
                ) {

                    // CACHE USER

                    sessionStorage.setItem(

                        "userRole",

                        data.user.role

                    );

                    sessionStorage.setItem(

                        "username",

                        data.user.username

                    );

                    // REDIRECT

                    window.location.href =
                    "/dashboard.html";

                }

                else {

                    alert(

                        data.error ||

                        "Login failed"

                    );

                }

            }

            catch (error) {

                console.error(
                    error
                );

                alert(
                    "Server error. Check Flask terminal."
                );

            }

        }

    );

});