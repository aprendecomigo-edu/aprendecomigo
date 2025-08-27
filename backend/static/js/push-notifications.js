/**
 * Push Notifications Handler for Aprende Comigo PWA
 * Handles subscription management and notification display
 */

class PushNotificationManager {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.subscription = null;
        this.vapidPublicKey = null;
        this.isSubscribed = false;
        
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.warn('Push notifications are not supported in this browser');
            this.hidePushUIElements();
            return;
        }

        try {
            // Get VAPID public key from server
            await this.getVapidPublicKey();
            
            // Check current subscription status
            await this.checkSubscriptionStatus();
            
            // Set up UI
            this.setupPushUI();
            
            // Handle notification clicks
            this.setupNotificationHandlers();
            
        } catch (error) {
            console.error('Failed to initialize push notifications:', error);
        }
    }

    async getVapidPublicKey() {
        try {
            const response = await fetch('/webpush/vapid_key/');
            if (response.ok) {
                const data = await response.json();
                this.vapidPublicKey = data.public_key;
                console.log('VAPID public key loaded successfully');
            } else {
                throw new Error('Failed to get VAPID public key');
            }
        } catch (error) {
            console.error('Error getting VAPID public key:', error);
            throw error;
        }
    }

    async checkSubscriptionStatus() {
        try {
            const registration = await navigator.serviceWorker.ready;
            this.subscription = await registration.pushManager.getSubscription();
            this.isSubscribed = this.subscription !== null;
            
            console.log('Push subscription status:', this.isSubscribed);
            
            if (this.isSubscribed) {
                console.log('User is subscribed to push notifications');
                await this.sendSubscriptionToServer(this.subscription);
            } else {
                console.log('User is not subscribed to push notifications');
            }
        } catch (error) {
            console.error('Error checking subscription status:', error);
        }
    }

    async subscribe() {
        try {
            if (!this.vapidPublicKey) {
                throw new Error('VAPID public key not available');
            }

            const registration = await navigator.serviceWorker.ready;
            
            // Request notification permission
            const permission = await Notification.requestPermission();
            
            if (permission === 'denied') {
                throw new Error('Notification permission denied');
            }
            
            if (permission === 'default') {
                throw new Error('Notification permission not granted');
            }

            // Subscribe to push notifications
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            console.log('User subscribed to push notifications:', subscription);

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);
            
            this.subscription = subscription;
            this.isSubscribed = true;
            this.updatePushUI();
            
            // Show success notification
            this.showNotification('Push notifications enabled! You\'ll receive important updates.', 'success');
            
            return subscription;

        } catch (error) {
            console.error('Failed to subscribe to push notifications:', error);
            this.showNotification(`Failed to enable notifications: ${error.message}`, 'error');
            throw error;
        }
    }

    async unsubscribe() {
        try {
            if (!this.subscription) {
                throw new Error('No subscription to unsubscribe from');
            }

            // Unsubscribe from push notifications
            await this.subscription.unsubscribe();
            
            // Remove subscription from server
            await this.removeSubscriptionFromServer(this.subscription);
            
            this.subscription = null;
            this.isSubscribed = false;
            this.updatePushUI();
            
            console.log('User unsubscribed from push notifications');
            this.showNotification('Push notifications disabled.', 'info');

        } catch (error) {
            console.error('Failed to unsubscribe from push notifications:', error);
            this.showNotification(`Failed to disable notifications: ${error.message}`, 'error');
            throw error;
        }
    }

    async sendSubscriptionToServer(subscription) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                             document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
            
            const response = await fetch('/webpush/save_information/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    subscription: subscription,
                    browser: this.getBrowserInfo()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Subscription sent to server successfully:', data);

        } catch (error) {
            console.error('Error sending subscription to server:', error);
            throw error;
        }
    }

    async removeSubscriptionFromServer(subscription) {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                             document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
            
            const response = await fetch('/webpush/unsubscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    subscription: subscription
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('Subscription removed from server successfully');

        } catch (error) {
            console.error('Error removing subscription from server:', error);
            throw error;
        }
    }

    setupPushUI() {
        // Create push notification toggle button
        const pushButton = document.getElementById('push-toggle-button');
        
        if (pushButton) {
            pushButton.addEventListener('click', () => this.togglePushSubscription());
            this.updatePushUI();
        } else {
            // Create push notification controls if they don't exist
            this.createPushUI();
        }
    }

    createPushUI() {
        // Check if we should show push notification prompt
        const container = document.getElementById('notification-container') || document.body;
        
        // Don't show if user has already dismissed or subscribed
        if (localStorage.getItem('push-prompt-dismissed') || this.isSubscribed) {
            return;
        }

        const pushPrompt = document.createElement('div');
        pushPrompt.id = 'push-notification-prompt';
        pushPrompt.className = 'fixed bottom-4 left-4 right-4 md:left-auto md:max-w-sm bg-white rounded-lg shadow-lg border p-4 z-50';
        pushPrompt.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5zM9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <div class="flex-1">
                    <h4 class="text-sm font-medium text-gray-900">Stay Updated</h4>
                    <p class="text-sm text-gray-600 mt-1">
                        Get notified about lesson reminders, assignments, and course updates.
                    </p>
                    <div class="mt-3 flex space-x-2">
                        <button id="enable-push-btn" 
                                class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded font-medium transition-colors">
                            Enable Notifications
                        </button>
                        <button id="dismiss-push-btn" 
                                class="bg-gray-200 hover:bg-gray-300 text-gray-800 text-xs px-3 py-1 rounded font-medium transition-colors">
                            Not Now
                        </button>
                    </div>
                </div>
                <button id="close-push-prompt" class="flex-shrink-0 text-gray-400 hover:text-gray-600">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;

        container.appendChild(pushPrompt);

        // Set up event listeners
        document.getElementById('enable-push-btn').addEventListener('click', async () => {
            try {
                await this.subscribe();
                pushPrompt.remove();
            } catch (error) {
                console.error('Error enabling push notifications:', error);
            }
        });

        document.getElementById('dismiss-push-btn').addEventListener('click', () => {
            localStorage.setItem('push-prompt-dismissed', 'true');
            pushPrompt.remove();
        });

        document.getElementById('close-push-prompt').addEventListener('click', () => {
            localStorage.setItem('push-prompt-dismissed', 'true');
            pushPrompt.remove();
        });

        // Auto-hide after 30 seconds
        setTimeout(() => {
            if (pushPrompt.parentNode) {
                localStorage.setItem('push-prompt-dismissed', 'true');
                pushPrompt.remove();
            }
        }, 30000);
    }

    updatePushUI() {
        const pushButton = document.getElementById('push-toggle-button');
        
        if (pushButton) {
            if (this.isSubscribed) {
                pushButton.textContent = 'Disable Notifications';
                pushButton.className = 'bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded font-medium transition-colors';
            } else {
                pushButton.textContent = 'Enable Notifications';
                pushButton.className = 'bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors';
            }
        }

        // Update settings page indicator
        const statusIndicator = document.getElementById('push-status-indicator');
        if (statusIndicator) {
            statusIndicator.textContent = this.isSubscribed ? 'Enabled' : 'Disabled';
            statusIndicator.className = this.isSubscribed ? 'text-green-600' : 'text-gray-500';
        }
    }

    async togglePushSubscription() {
        try {
            if (this.isSubscribed) {
                await this.unsubscribe();
            } else {
                await this.subscribe();
            }
        } catch (error) {
            console.error('Error toggling push subscription:', error);
        }
    }

    setupNotificationHandlers() {
        // Handle notification click events (via service worker message)
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'NOTIFICATION_CLICKED') {
                    this.handleNotificationClick(event.data);
                }
            });
        }

        // Handle service worker messages
        navigator.serviceWorker.addEventListener('message', (event) => {
            const { type, data } = event.data || {};
            
            switch (type) {
                case 'PUSH_RECEIVED':
                    console.log('Push notification received:', data);
                    break;
                case 'NOTIFICATION_CLICKED':
                    this.handleNotificationClick(data);
                    break;
                case 'NOTIFICATION_CLOSED':
                    console.log('Notification closed:', data);
                    break;
            }
        });
    }

    handleNotificationClick(data) {
        const { action, notificationData } = data;
        
        console.log('Notification clicked:', action, notificationData);
        
        // Handle different notification actions
        switch (action) {
            case 'view_course':
            case 'view_assignment':
            case 'view_lesson':
            case 'join_lesson':
                if (notificationData.url) {
                    window.location.href = notificationData.url;
                }
                break;
            case 'view_schedule':
                window.location.href = '/education/schedule/';
                break;
            case 'view_payments':
                window.location.href = '/education/payments/history/';
                break;
            default:
                // Default action - open the URL from notification data
                if (notificationData.url) {
                    window.location.href = notificationData.url;
                }
                break;
        }
    }

    hidePushUIElements() {
        const elements = document.querySelectorAll('.push-notification-feature');
        elements.forEach(el => el.style.display = 'none');
    }

    getBrowserInfo() {
        const userAgent = navigator.userAgent;
        let browser = 'Unknown';
        
        if (userAgent.includes('Chrome')) browser = 'Chrome';
        else if (userAgent.includes('Firefox')) browser = 'Firefox';
        else if (userAgent.includes('Safari')) browser = 'Safari';
        else if (userAgent.includes('Edge')) browser = 'Edge';
        
        return browser;
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    showNotification(message, type = 'info') {
        if (window.pwaCore && window.pwaCore.showNotification) {
            window.pwaCore.showNotification(message, type);
        } else {
            console.log(`Notification (${type}): ${message}`);
        }
    }

    // Test push notification (for development/testing)
    async sendTestNotification() {
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                             document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
            
            const response = await fetch('/webpush/send_push/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    head: 'Test Notification',
                    body: 'This is a test push notification from Aprende Comigo!',
                    icon: '/static/images/icon-192x192.png',
                    url: '/'
                })
            });

            if (response.ok) {
                console.log('Test notification sent successfully');
                this.showNotification('Test notification sent!', 'success');
            } else {
                throw new Error('Failed to send test notification');
            }

        } catch (error) {
            console.error('Error sending test notification:', error);
            this.showNotification('Failed to send test notification', 'error');
        }
    }
}

// Initialize push notification manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.pushNotificationManager = new PushNotificationManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PushNotificationManager;
}