/**
 * PWA Core JavaScript
 * Handles service worker registration, offline detection, and PWA features
 */

// Production logging utility
const DEBUG = false; // Set to false for production
const log = DEBUG ? console.log.bind(console, '[PWA]') : () => {};
const warn = DEBUG ? console.warn.bind(console, '[PWA]') : () => {};
const error = console.error.bind(console, '[PWA]'); // Always log errors

class PWACore {
    constructor() {
        this.isOnline = navigator.onLine;
        this.serviceWorker = null;
        this.installPrompt = null;
        
        this.init();
    }

    async init() {
        // Service Worker Registration
        if ('serviceWorker' in navigator) {
            try {
                this.serviceWorker = await navigator.serviceWorker.register('/sw.js');
                log('Service Worker registered successfully');
                
                // Listen for service worker updates
                this.serviceWorker.addEventListener('updatefound', () => {
                    this.handleServiceWorkerUpdate();
                });
            } catch (error) {
                error('Service Worker registration failed:', error);
            }
        }

        // Online/Offline Detection
        window.addEventListener('online', () => this.handleOnlineStatus(true));
        window.addEventListener('offline', () => this.handleOnlineStatus(false));

        // PWA Install Prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.installPrompt = e;
            this.showInstallButton();
        });

        // Check if running as PWA
        if (window.matchMedia('(display-mode: standalone)').matches) {
            document.body.classList.add('pwa-standalone');
        }

        // Initialize offline indicator
        this.updateOfflineIndicator();
    }

    handleOnlineStatus(online) {
        this.isOnline = online;
        this.updateOfflineIndicator();
        
        if (online) {
            this.syncPendingData();
        }
    }

    updateOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.style.display = this.isOnline ? 'none' : 'block';
        }
        
        document.body.classList.toggle('offline', !this.isOnline);
    }

    handleServiceWorkerUpdate() {
        const updateBanner = document.getElementById('update-banner');
        if (updateBanner) {
            updateBanner.style.display = 'block';
        }
    }

    async refreshApp() {
        if (this.serviceWorker && this.serviceWorker.waiting) {
            this.serviceWorker.waiting.postMessage({ type: 'SKIP_WAITING' });
            window.location.reload();
        }
    }

    showInstallButton() {
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', () => this.installPWA());
        }
    }

    async installPWA() {
        if (this.installPrompt) {
            this.installPrompt.prompt();
            const result = await this.installPrompt.userChoice;
            
            if (result.outcome === 'accepted') {
                log('PWA installation accepted');
            }
            
            this.installPrompt = null;
            this.hideInstallButton();
        }
    }

    hideInstallButton() {
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }

    // Offline Data Sync
    async syncPendingData() {
        try {
            // Sync any cached form submissions
            const pendingForms = await this.getPendingFormData();
            
            for (const formData of pendingForms) {
                await this.submitCachedForm(formData);
            }
            
            // Sync enrollment attempts
            const pendingEnrollments = await this.getPendingEnrollments();
            
            for (const enrollment of pendingEnrollments) {
                await this.submitCachedEnrollment(enrollment);
            }
            
        } catch (error) {
            error('Data sync failed:', error);
        }
    }

    async getPendingFormData() {
        const cache = await caches.open('form-submissions-v1');
        const keys = await cache.keys();
        const pendingData = [];
        
        for (const request of keys) {
            const response = await cache.match(request);
            const data = await response.json();
            pendingData.push(data);
        }
        
        return pendingData;
    }

    async submitCachedForm(formData) {
        try {
            const response = await fetch(formData.url, {
                method: formData.method,
                headers: formData.headers,
                body: formData.body
            });
            
            if (response.ok) {
                // Remove from cache after successful submission
                const cache = await caches.open('form-submissions-v1');
                await cache.delete(formData.url);
                
                // Show success notification
                this.showNotification('Data synced successfully', 'success');
            }
        } catch (error) {
            error('Failed to submit cached form:', error);
        }
    }

    async getPendingEnrollments() {
        // Implementation for enrollment-specific data
        return [];
    }

    async submitCachedEnrollment(enrollment) {
        // Implementation for enrollment-specific submission
        return;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add to notification container
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Background Sync for form submissions
    async cacheFormSubmission(url, method, headers, body) {
        if (!this.isOnline) {
            const cache = await caches.open('form-submissions-v1');
            const request = new Request(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    method,
                    headers,
                    body,
                    timestamp: Date.now()
                })
            });
            
            await cache.put(request, new Response(JSON.stringify({
                url, method, headers, body, cached: true
            })));
            
            this.showNotification('Data saved offline. Will sync when online.', 'info');
            return true;
        }
        return false;
    }
}

// Initialize PWA Core
document.addEventListener('DOMContentLoaded', () => {
    window.pwaCore = new PWACore();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWACore;
}