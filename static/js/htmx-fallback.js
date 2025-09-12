/**
 * Minimal HTMX fallback for when CDN is blocked
 * Provides basic form submission via AJAX
 */
(function() {
    'use strict';
    
    // Simple HTMX-like functionality
    function handleHtmxForms() {
        const forms = document.querySelectorAll('[hx-post]');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const url = form.getAttribute('hx-post');
                const target = form.getAttribute('hx-target');
                const swap = form.getAttribute('hx-swap') || 'innerHTML';
                
                // Get form data
                const formData = new FormData(form);
                
                // Show loading state
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.classList.add('htmx-request');
                }
                
                // Make AJAX request
                fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    }
                })
                .then(response => response.text())
                .then(html => {
                    if (target) {
                        const targetEl = document.querySelector(target);
                        if (targetEl) {
                            if (swap === 'innerHTML') {
                                targetEl.innerHTML = html;
                            } else if (swap === 'outerHTML') {
                                targetEl.outerHTML = html;
                            }
                            // Re-initialize forms in the new content
                            handleHtmxForms();
                        }
                    }
                })
                .catch(error => {
                    console.error('HTMX fallback error:', error);
                    // Show error message
                    const errorAlert = document.getElementById('error-alert');
                    const errorMessage = document.getElementById('error-message');
                    if (errorAlert && errorMessage) {
                        errorMessage.textContent = 'Something went wrong. Please try again.';
                        errorAlert.classList.remove('hidden');
                    }
                })
                .finally(() => {
                    // Remove loading state
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('htmx-request');
                    }
                });
            });
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', handleHtmxForms);
    } else {
        handleHtmxForms();
    }
    
    // Expose minimal HTMX-like API
    window.htmx = window.htmx || {
        process: handleHtmxForms,
        trigger: function(element, event) {
            if (element && typeof element.dispatchEvent === 'function') {
                element.dispatchEvent(new Event(event, { bubbles: true }));
            }
        }
    };
})();