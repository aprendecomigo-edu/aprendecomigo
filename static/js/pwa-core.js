/**
 * PWA Core JavaScript - Essential functionality for Progressive Web App
 */

// PWA Core functionality
class PWACore {
    constructor() {
        this.isInstallable = false;
        this.deferredPrompt = null;
        this.init();
    }

    init() {
        this.registerServiceWorker();
        this.setupInstallPrompt();
        this.setupOfflineDetection();
    }

    // Register Service Worker
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered:', registration);
                
                // Listen for SW updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    if (newWorker) {
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                this.showUpdateNotification();
                            }
                        });
                    }
                });
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    // Setup install prompt handling
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.isInstallable = true;
            this.showInstallButton();
        });

        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.hideInstallButton();
            this.deferredPrompt = null;
        });
    }

    // Setup offline detection
    setupOfflineDetection() {
        window.addEventListener('online', () => {
            this.hideOfflineNotification();
            document.body.classList.remove('offline');
        });

        window.addEventListener('offline', () => {
            this.showOfflineNotification();
            document.body.classList.add('offline');
        });

        // Initial state
        if (!navigator.onLine) {
            document.body.classList.add('offline');
        }
    }

    // Show install button
    showInstallButton() {
        const installBtn = document.getElementById('install-btn');
        if (installBtn) {
            installBtn.style.display = 'block';
            installBtn.addEventListener('click', () => this.installApp());
        }
    }

    // Hide install button
    hideInstallButton() {
        const installBtn = document.getElementById('install-btn');
        if (installBtn) {
            installBtn.style.display = 'none';
        }
    }

    // Install the app
    async installApp() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            
            this.deferredPrompt = null;
            this.hideInstallButton();
        }
    }

    // Show update notification
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <span>A new version is available!</span>
                <button onclick="pwaCore.reloadApp()">Update</button>
                <button onclick="this.parentElement.parentElement.remove()">Later</button>
            </div>
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
        `;
        document.body.appendChild(notification);
    }

    // Show offline notification
    showOfflineNotification() {
        let notification = document.getElementById('offline-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'offline-notification';
            notification.innerHTML = 'You are currently offline. Some features may be limited.';
            notification.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #f44336;
                color: white;
                padding: 10px;
                text-align: center;
                z-index: 1000;
            `;
            document.body.appendChild(notification);
        }
    }

    // Hide offline notification
    hideOfflineNotification() {
        const notification = document.getElementById('offline-notification');
        if (notification) {
            notification.remove();
        }
    }

    // Reload app to get updates
    reloadApp() {
        window.location.reload();
    }

    // Get app info
    getAppInfo() {
        return {
            isInstallable: this.isInstallable,
            isOnline: navigator.onLine,
            isStandalone: window.matchMedia('(display-mode: standalone)').matches,
            hasServiceWorker: 'serviceWorker' in navigator
        };
    }
}

// Initialize PWA Core when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.pwaCore = new PWACore();
    
    // Add install button if not already present
    if (!document.getElementById('install-btn')) {
        const installBtn = document.createElement('button');
        installBtn.id = 'install-btn';
        installBtn.innerHTML = '📱 Install App';
        installBtn.style.cssText = `
            display: none;
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #2196F3;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 5px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
        `;
        document.body.appendChild(installBtn);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWACore;
}