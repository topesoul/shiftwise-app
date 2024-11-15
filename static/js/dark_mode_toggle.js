// /workspace/shiftwise/static/js/dark_mode_toggle.js

document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('darkModeToggle');
    const body = document.body;

    // Check for saved user preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        body.classList.add('dark-mode');
    }

    toggle.addEventListener('click', function(e) {
        e.preventDefault();
        body.classList.toggle('dark-mode');
        // Save user preference
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('darkMode', 'enabled');
        } else {
            localStorage.setItem('darkMode', 'disabled');
        }
    });
});
