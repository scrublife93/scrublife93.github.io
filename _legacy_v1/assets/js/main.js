// Theme Toggle Logic
const toggleButton = document.getElementById('theme-toggle');
const body = document.body;
const icon = toggleButton ? toggleButton.querySelector('i') : null;

// Check local storage
const currentTheme = localStorage.getItem('theme');
if (currentTheme) {
    body.setAttribute('data-theme', currentTheme);
    updateIcon(currentTheme);
}

// Toggle Event
if (toggleButton) {
    toggleButton.addEventListener('click', () => {
        let theme = body.getAttribute('data-theme');
        if (theme === 'light') {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            updateIcon('dark');
        } else {
            body.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            updateIcon('light');
        }
    });
}

function updateIcon(theme) {
    if (!icon) return;
    if (theme === 'light') {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
}
