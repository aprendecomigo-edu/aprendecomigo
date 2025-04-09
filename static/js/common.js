document.addEventListener('DOMContentLoaded', function() {
    // Set CSRF token for all HTMX requests
    htmx.config.headers['X-CSRFToken'] = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Add loading indicators for HTMX requests
    htmx.on('htmx:beforeSend', function(evt) {
        let target = evt.detail.target;
        if (target.querySelector('.htmx-indicator')) {
            target.querySelector('.htmx-indicator').classList.add('htmx-request');
        }
    });

    htmx.on('htmx:afterSettle', function(evt) {
        let target = evt.detail.target;
        if (target.querySelector('.htmx-indicator')) {
            target.querySelector('.htmx-indicator').classList.remove('htmx-request');
        }
    });

    // Theme toggling functionality
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Check if user has a theme preference stored
        const currentTheme = localStorage.getItem('theme') || 'light';
        if (currentTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggle.querySelector('i').classList.remove('fa-moon');
            themeToggle.querySelector('i').classList.add('fa-sun');
        }

        // Toggle theme when the toggle button is clicked
        themeToggle.addEventListener('click', function() {
            const isDarkTheme = document.body.classList.toggle('dark-theme');
            const icon = themeToggle.querySelector('i');

            if (isDarkTheme) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
                localStorage.setItem('theme', 'dark');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
                localStorage.setItem('theme', 'light');
            }
        });
    }
});
