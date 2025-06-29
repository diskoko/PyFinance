/**
 * Notification System for Financial Application
 * Provides toast-style notifications with different types and auto-dismiss
 */

// Create notification container if it doesn't exist
function createNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    return container;
}

// Show notification with specified type and message
function showNotification(type, message, duration = 5000) {
    const container = createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type.toLowerCase()}`;
    
    // Create notification content
    const icon = getNotificationIcon(type);
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icon}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="closeNotification(this.parentElement.parentElement)">×</button>
        </div>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Trigger entrance animation
    setTimeout(() => {
        notification.classList.add('notification-show');
    }, 10);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            closeNotification(notification);
        }, duration);
    }
    
    return notification;
}

// Get appropriate icon for notification type
function getNotificationIcon(type) {
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'loading': '⏳'
    };
    return icons[type.toLowerCase()] || '📢';
}

// Close notification with animation
function closeNotification(notification) {
    if (notification && notification.parentElement) {
        notification.classList.add('notification-exit');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
            }
        }, 300);
    }
}

// Show success notification
function showSuccess(message, duration) {
    return showNotification('success', message, duration);
}

// Show error notification
function showError(message, duration) {
    return showNotification('error', message, duration);
}

// Show warning notification
function showWarning(message, duration) {
    return showNotification('warning', message, duration);
}

// Show info notification
function showInfo(message, duration) {
    return showNotification('info', message, duration);
}

// Show loading notification (doesn't auto-dismiss)
function showLoading(message) {
    return showNotification('loading', message, 0);
}

// Clear all notifications
function clearAllNotifications() {
    const container = document.getElementById('notification-container');
    if (container) {
        container.innerHTML = '';
    }
}

// Initialize notification system
document.addEventListener('DOMContentLoaded', function() {
    createNotificationContainer();
    
    // Add keyboard support for closing notifications
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            clearAllNotifications();
        }
    });
});
