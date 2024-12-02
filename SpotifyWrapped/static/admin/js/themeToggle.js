document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("themeToggle");
    const currentTheme = localStorage.getItem("theme");

    // Default to dark mode
    if (currentTheme === "light") {
        document.body.classList.add("light-mode");
        toggle.checked = true; // Set the toggle for light mode
    }

    toggle.addEventListener("change", () => {
        if (toggle.checked) {
            document.body.classList.add("light-mode");
            localStorage.setItem("theme", "light");
        } else {
            document.body.classList.remove("light-mode");
            localStorage.setItem("theme", "dark");
        }
    });
});
