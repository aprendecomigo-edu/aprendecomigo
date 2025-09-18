/**
 * PWA Detection and Session Management Client-Side Support
 *
 * This module provides comprehensive client-side PWA detection to support
 * the backend SessionManagementMiddleware with differentiated session durations:
 * - Web browser: 24 hours
 * - PWA installation: 7 days
 *
 * Features:
 * - Multiple PWA detection strategies with fallback
 * - Cookie management for PWA state
 * - Fetch interception to add PWA headers
 * - Real-time display mode change detection
 *
 * Business Requirements:
 * - FR-4.1: Web browser sessions = 24 hours
 * - FR-4.2: PWA installation sessions = 7 days
 * - FR-4.3: Automatic session extension based on activity
 * - FR-4.4: Secure session management with proper headers
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        COOKIE_NAME: 'pwa_mode',
        COOKIE_MAX_AGE: 365 * 24 * 60 * 60, // 1 year in seconds
        DEBUG: false, // Set to true for development debugging
        DETECTION_INTERVAL: 1000, // Check for display mode changes every second
    };

    // PWA Detection Utilities
    const PWADetection = {
        /**
         * Comprehensive PWA detection using multiple strategies
         * @returns {boolean} True if running as PWA
         */
        isPWA: function() {
            // Strategy 1: Display mode detection (most reliable for modern browsers)
            if (this.checkDisplayMode()) {
                this.log('PWA detected via display mode');
                return true;
            }

            // Strategy 2: iOS Safari standalone detection
            if (this.checkiOSStandalone()) {
                this.log('PWA detected via iOS standalone mode');
                return true;
            }

            // Strategy 3: Android Chrome PWA detection
            if (this.checkAndroidPWA()) {
                this.log('PWA detected via Android PWA indicators');
                return true;
            }

            // Strategy 4: PWA-specific viewport detection
            if (this.checkPWAViewport()) {
                this.log('PWA detected via viewport meta tag');
                return true;
            }

            // Default: treat as web browser
            this.log('Request classified as web browser');
            return false;
        },

        /**
         * Check if display-mode: standalone is active
         * @returns {boolean} True if in standalone mode
         */
        checkDisplayMode: function() {
            if (window.matchMedia) {
                return window.matchMedia('(display-mode: standalone)').matches ||
                       window.matchMedia('(display-mode: fullscreen)').matches ||
                       window.matchMedia('(display-mode: minimal-ui)').matches;
            }
            return false;
        },

        /**
         * Check iOS Safari standalone mode
         * @returns {boolean} True if iOS PWA
         */
        checkiOSStandalone: function() {
            return window.navigator.standalone === true;
        },

        /**
         * Check Android Chrome PWA indicators
         * @returns {boolean} True if Android PWA
         */
        checkAndroidPWA: function() {
            // Check for Chrome app installation
            if (window.chrome && window.chrome.app && window.chrome.app.isInstalled) {
                return true;
            }

            // Check if running in WebView context
            const userAgent = navigator.userAgent;
            if (userAgent.includes('wv') && userAgent.includes('Mobile')) {
                return true;
            }

            return false;
        },

        /**
         * Check for PWA-specific viewport meta tag
         * @returns {boolean} True if PWA viewport detected
         */
        checkPWAViewport: function() {
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            if (viewportMeta) {
                const content = viewportMeta.getAttribute('content') || '';
                // PWAs often have viewport-fit=cover for fullscreen experience
                return content.includes('viewport-fit=cover');
            }
            return false;
        },

        /**
         * Debug logging utility
         * @param {string} message Log message
         */
        log: function(message) {
            if (CONFIG.DEBUG) {
                console.log('[PWA Detection]', message);
            }
        }
    };

    // Cookie Management
    const CookieManager = {
        /**
         * Set PWA mode cookie
         * @param {boolean} isPWA Whether running as PWA
         */
        setPWAModeCookie: function(isPWA) {
            const mode = isPWA ? 'standalone' : 'browser';
            const expires = new Date();
            expires.setTime(expires.getTime() + (CONFIG.COOKIE_MAX_AGE * 1000));

            const cookieValue = `${CONFIG.COOKIE_NAME}=${mode}; ` +
                              `expires=${expires.toUTCString()}; ` +
                              `path=/; ` +
                              `SameSite=Strict; ` +
                              (location.protocol === 'https:' ? 'Secure' : '');

            document.cookie = cookieValue;
            PWADetection.log(`Cookie set: ${mode} mode`);
        },

        /**
         * Get current PWA mode from cookie
         * @returns {string|null} 'standalone', 'browser', or null
         */
        getPWAModeCookie: function() {
            const name = CONFIG.COOKIE_NAME + '=';
            const decodedCookie = decodeURIComponent(document.cookie);
            const cookieArray = decodedCookie.split(';');

            for (let i = 0; i < cookieArray.length; i++) {
                let cookie = cookieArray[i];
                while (cookie.charAt(0) === ' ') {
                    cookie = cookie.substring(1);
                }
                if (cookie.indexOf(name) === 0) {
                    return cookie.substring(name.length, cookie.length);
                }
            }
            return null;
        }
    };

    // Fetch Interception for PWA Headers
    const FetchInterceptor = {
        /**
         * Initialize fetch interception to add PWA headers
         */
        init: function() {
            // Store original fetch
            const originalFetch = window.fetch;

            // Override fetch to add PWA headers
            window.fetch = function(...args) {
                const [resource, config] = args;

                // Create headers if not present
                const headers = new Headers(config?.headers || {});

                // Add PWA detection headers
                const isPWA = PWADetection.isPWA();
                if (isPWA) {
                    headers.set('X-PWA-Mode', 'standalone');
                    headers.set('X-Standalone-Mode', '1');
                } else {
                    headers.set('X-PWA-Mode', 'browser');
                    headers.set('X-Standalone-Mode', '0');
                }

                // Update config
                const newConfig = {
                    ...config,
                    headers: headers
                };

                PWADetection.log(`Fetch request with PWA headers: ${isPWA ? 'standalone' : 'browser'}`);

                // Call original fetch with modified headers
                return originalFetch.apply(this, [resource, newConfig]);
            };
        }
    };

    // Display Mode Change Monitoring
    const DisplayModeMonitor = {
        currentMode: null,

        /**
         * Initialize display mode monitoring
         */
        init: function() {
            this.currentMode = PWADetection.isPWA();
            this.startMonitoring();
        },

        /**
         * Start monitoring for display mode changes
         */
        startMonitoring: function() {
            // Use matchMedia for modern browsers
            if (window.matchMedia) {
                const standaloneQuery = window.matchMedia('(display-mode: standalone)');
                if (standaloneQuery.addEventListener) {
                    standaloneQuery.addEventListener('change', this.handleModeChange.bind(this));
                } else if (standaloneQuery.addListener) {
                    standaloneQuery.addListener(this.handleModeChange.bind(this));
                }
            }

            // Fallback polling for broader compatibility
            setInterval(() => {
                const newMode = PWADetection.isPWA();
                if (newMode !== this.currentMode) {
                    this.handleModeChange({ matches: newMode });
                }
            }, CONFIG.DETECTION_INTERVAL);
        },

        /**
         * Handle display mode changes
         * @param {Event} event MediaQuery change event
         */
        handleModeChange: function(event) {
            const newMode = PWADetection.isPWA();
            if (newMode !== this.currentMode) {
                this.currentMode = newMode;
                PWADetection.log(`Display mode changed to: ${newMode ? 'PWA' : 'browser'}`);

                // Update cookie
                CookieManager.setPWAModeCookie(newMode);

                // Optionally trigger a page refresh to update session
                // Uncomment if you want immediate session reconfiguration
                // window.location.reload();
            }
        }
    };

    // Main Initialization
    const PWAManager = {
        /**
         * Initialize PWA detection and management
         */
        init: function() {
            PWADetection.log('Initializing PWA detection system');

            // Detect initial PWA mode
            const isPWA = PWADetection.isPWA();

            // Set initial cookie
            CookieManager.setPWAModeCookie(isPWA);

            // Initialize fetch interception
            FetchInterceptor.init();

            // Initialize display mode monitoring
            DisplayModeMonitor.init();

            // Log initial state
            PWADetection.log(`Initial PWA state: ${isPWA ? 'standalone' : 'browser'}`);

            // Debug information
            if (CONFIG.DEBUG) {
                this.logDebugInfo();
            }
        },

        /**
         * Log debug information about PWA detection
         */
        logDebugInfo: function() {
            const debugInfo = {
                displayMode: window.matchMedia ? {
                    standalone: window.matchMedia('(display-mode: standalone)').matches,
                    fullscreen: window.matchMedia('(display-mode: fullscreen)').matches,
                    minimalUI: window.matchMedia('(display-mode: minimal-ui)').matches,
                } : 'not supported',
                iosStandalone: window.navigator.standalone,
                userAgent: navigator.userAgent,
                chrome: !!window.chrome,
                currentCookie: CookieManager.getPWAModeCookie(),
                isPWA: PWADetection.isPWA()
            };

            console.log('[PWA Debug Info]', debugInfo);
        }
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', PWAManager.init.bind(PWAManager));
    } else {
        PWAManager.init();
    }

    // Export for manual usage if needed
    window.PWADetection = PWADetection;
    window.PWAManager = PWAManager;

})();
