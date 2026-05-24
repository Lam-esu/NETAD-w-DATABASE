document.addEventListener(
    "DOMContentLoaded",

    function () {

        console.log(
            "login.js loaded"
        );

        const loginForm =

        document.getElementById(
            "loginForm"
        );

        const message =

        document.getElementById(
            "message"
        );

        if (
            !loginForm
        ) {

            console.error(
                "loginForm not found"
            );

            return;

        }

        loginForm
        .addEventListener(

            "submit",

            async function (
                e
            ) {

                e.preventDefault();

                const username =

                document
                .getElementById(
                    "username"
                )

                .value;

                const password =

                document
                .getElementById(
                    "password"
                )

                .value;

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

                            JSON.stringify(

                                {
                                    username,
                                    password
                                }

                            )

                        }

                    );

                    const data =

                    await response
                    .json();

                    console.log(
                        data
                    );

                    if (

                        response.ok

                    ) {

                        // CACHE USER

                        sessionStorage
                        .setItem(

                            "userRole",

                            data.user.role

                        );

                        sessionStorage
                        .setItem(

                            "username",

                            data.user.username

                        );

                        message.textContent =

                        "Login successful";

                        // FAST REDIRECT

                        window.location.replace(

                            "/dashboard.html"

                        );

                    }

                    else {

                        message.textContent =

                        data.error ||

                        "Login failed";

                    }

                }

                catch (

                    error

                ) {

                    console.error(
                        error
                    );

                    message.textContent =

                    "Server error";

                }

            }

        );

    }
);