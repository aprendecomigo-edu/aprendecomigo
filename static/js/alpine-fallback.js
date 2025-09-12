/**
 * Minimal Alpine.js fallback for when CDN is blocked
 * Provides basic reactive functionality
 */
(function() {
    'use strict';
    
    // Simple Alpine-like functionality
    function initAlpine() {
        // Handle x-data attributes
        const dataElements = document.querySelectorAll('[x-data]');
        dataElements.forEach(el => {
            try {
                const dataScript = el.getAttribute('x-data');
                if (dataScript && dataScript.trim()) {
                    // Simple evaluation of data - only handle basic object literals
                    const data = eval('(' + dataScript + ')');
                    el._alpineData = data;
                }
            } catch (e) {
                console.warn('Alpine fallback: Could not parse x-data:', e);
            }
        });
        
        // Handle x-show attributes
        const showElements = document.querySelectorAll('[x-show]');
        showElements.forEach(el => {
            const showScript = el.getAttribute('x-show');
            if (showScript) {
                try {
                    // Simple boolean evaluation
                    const show = showScript === 'true' || showScript === '!false';
                    el.style.display = show ? '' : 'none';
                } catch (e) {
                    console.warn('Alpine fallback: Could not evaluate x-show:', e);
                }
            }
        });
        
        // Handle x-click attributes for basic event handling
        const clickElements = document.querySelectorAll('[x-click]');
        clickElements.forEach(el => {
            const clickScript = el.getAttribute('x-click');
            if (clickScript) {
                el.addEventListener('click', function() {
                    try {
                        // Very basic function execution
                        if (clickScript.includes('()')) {
                            eval(clickScript);
                        }
                    } catch (e) {
                        console.warn('Alpine fallback: Could not execute x-click:', e);
                    }
                });
            }
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAlpine);
    } else {
        initAlpine();
    }
    
    // Expose minimal Alpine-like API
    window.Alpine = window.Alpine || {
        start: initAlpine,
        data: function(name, callback) {
            // Basic data registration
            console.log('Alpine fallback: data registered for', name);
        }
    };
})();