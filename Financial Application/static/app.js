/**
 * Journal Application JavaScript
 * Handles UI interactivity including calendar navigation,
 * dark/light mode toggling, and entry panel interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize navigation buttons
    setupNavigationButtons();
    
    // Setup dark/light mode toggle
    setupDarkModeToggle();
    
    // Setup entry panel interactions
    setupEntryPanels();
    
    // Initialize the calendar (if present)
    if (document.querySelector('.calendar')) {
        renderCalendar();
    }
    
    // Setup goal update forms
    setupGoalUpdateForms();

    // Update financial status on load
    updateFinancialStatus();

    // Enhance navigation and setup tooltips
    enhanceNavigation();
    setupTooltips();
});

/**
 * Sets up the navigation buttons (prev/next)
 */
function setupNavigationButtons() {
    const navButtons = document.querySelectorAll('.nav-arrow');
    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            // TODO: Replace this with actual date navigation
            alert('Navigation button clicked! This will navigate to the previous/next day.');
        });
    });
}

/**
 * Sets up the dark/light mode toggle functionality
 * Preserves user preference in localStorage
 */
function setupDarkModeToggle() {
    const themeToggle = document.querySelector('#theme-toggle');
    const bodyElement = document.body;

    // Load saved preference from localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        bodyElement.classList.add(savedTheme);
    } else {
        // Default to light mode
        bodyElement.classList.add('light-mode');
        localStorage.setItem('theme', 'light-mode');
    }

    // Add click event listener to toggle button
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            if (bodyElement.classList.contains('dark-mode')) {
                bodyElement.classList.remove('dark-mode');
                bodyElement.classList.add('light-mode');
                localStorage.setItem('theme', 'light-mode');
                if (typeof showNotification === 'function') {
                    showNotification('info', 'Switched to light mode ☀️', 2000);
                }
            } else {
                bodyElement.classList.remove('light-mode');
                bodyElement.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark-mode');
                if (typeof showNotification === 'function') {
                    showNotification('info', 'Switched to dark mode 🌙', 2000);
                }
            }
        });
    }
}

/**
 * Sets up expandable/collapsible entry panels
 */
function setupEntryPanels() {
    const entryPanels = document.querySelectorAll('.entry-panel');
    entryPanels.forEach(panel => {
        panel.addEventListener('click', () => {
            panel.classList.toggle('active');
        });
    });
}

/**
 * Renders the calendar with the current month
 * Highlights today and days with journal entries
 */
function renderCalendar() {
    const monthYearDisplay = document.getElementById('monthYear');
    const daysContainer = document.querySelector('.days');
    
    // Clear previous days
    daysContainer.innerHTML = '';

    // Update month and year display
    const currentMonth = selectedDate.getMonth();
    const currentYear = selectedDate.getFullYear();
    monthYearDisplay.innerHTML = `${selectedDate.toLocaleString('default', { month: 'long' })}<br><span style="font-size:18px">${currentYear}</span>`;

    // Get first day of month and last date
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();
    const lastDateOfMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    // Generate calendar days
    for (let dayNum = 1; dayNum <= lastDateOfMonth; dayNum++) {
        const dayElement = document.createElement('li');
        dayElement.innerText = dayNum;
        
        // Highlight current day
        if (dayNum === currentDate.getDate() && 
            currentMonth === currentDate.getMonth() && 
            currentYear === currentDate.getFullYear()) {
            dayElement.classList.add('current-day');
        }
        
        // Highlight days with entries
        if (entryDays.includes(dayNum)) {
            dayElement.classList.add('entry-day');
        }
        
        // Make days clickable
        dayElement.onclick = () => selectDate(dayNum);
        daysContainer.appendChild(dayElement);
    }
}

/**
 * Shows a notification message
 * @param {string} title - The title of the notification
 * @param {string} message - The message content of the notification
 */
function showNotification(title, message) {
    // Create container if it doesn't exist
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <div class="notification-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                <path d="M8 12L11 15L16 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        </div>
    `;

    // Add to container
    container.appendChild(notification);

    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 100);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Sets up goal update forms with proper error handling and notifications
 */
function setupGoalUpdateForms() {
    document.querySelectorAll('.update-form').forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const goalId = this.dataset.goalId;
            const formData = new FormData(this);
            const errorDiv = this.querySelector('.error-message');
            const submitBtn = this.querySelector('button[type="submit"]');
            
            // Show loading state
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Updating...';
            }
            
            try {
                const response = await fetch(`/update_goal/${goalId}`, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    if (typeof showSuccess === 'function') {
                        showSuccess(data.message);
                    }
                    this.reset();
                    // Refresh page to show updated goals
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    if (errorDiv) {
                        errorDiv.textContent = data.message;
                        errorDiv.style.display = 'block';
                    }
                    if (typeof showError === 'function') {
                        showError(data.message);
                    }
                }
            } catch (error) {
                const errorMessage = 'Failed to update goal. Please try again.';
                if (errorDiv) {
                    errorDiv.textContent = errorMessage;
                    errorDiv.style.display = 'block';
                }
                if (typeof showError === 'function') {
                    showError(errorMessage);
                }
            } finally {
                // Reset button state
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Update';
                }
            }
        });
    });
}

// Enhanced form validation
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    return isValid;
}

// Add real-time validation
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            field.addEventListener('blur', function() {
                if (!this.value.trim()) {
                    this.classList.add('error');
                } else {
                    this.classList.remove('error');
                }
            });
            
            field.addEventListener('input', function() {
                if (this.classList.contains('error') && this.value.trim()) {
                    this.classList.remove('error');
                }
            });
        });
        
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                if (typeof showWarning === 'function') {
                    showWarning('Please fill in all required fields.');
                }
            }
        });
    });
}

/**
 * Load and update financial status
 */
async function loadFinancialStatus() {
    try {
        const response = await fetch('/api/financial_status');
        const data = await response.json();
        
        // Update main dashboard status
        const statusElements = {
            emoji: document.getElementById('status-emoji'),
            message: document.getElementById('status-message'),
            icon: document.getElementById('status-icon')
        };
        
        if (statusElements.emoji) statusElements.emoji.textContent = data.status_icon;
        if (statusElements.message) statusElements.message.textContent = data.status_text;
        if (statusElements.icon) statusElements.icon.textContent = data.status_icon;
        
        // Update sidebar financial overview
        const sidebarIcon = document.getElementById('sidebar-status-icon');
        const sidebarText = document.getElementById('sidebar-status-text');
        const sidebarGoals = document.getElementById('sidebar-goals-completed');
        const sidebarBudget = document.getElementById('sidebar-budget-status');
        const sidebarActivity = document.getElementById('sidebar-recent-activity');
        
        if (sidebarIcon) sidebarIcon.textContent = data.status_icon;
        if (sidebarText) sidebarText.textContent = data.status_text;
        if (sidebarGoals) sidebarGoals.textContent = `${data.completed_goals}/${data.total_goals}`;
        if (sidebarBudget) sidebarBudget.textContent = `${data.budget_utilization}%`;
        if (sidebarActivity) sidebarActivity.textContent = data.recent_activity;
        
    } catch (error) {
        console.error('Error loading financial status:', error);
        
        // Fallback values for sidebar
        const sidebarIcon = document.getElementById('sidebar-status-icon');
        const sidebarText = document.getElementById('sidebar-status-text');
        const sidebarGoals = document.getElementById('sidebar-goals-completed');
        const sidebarBudget = document.getElementById('sidebar-budget-status');
        const sidebarActivity = document.getElementById('sidebar-recent-activity');
        
        if (sidebarIcon) sidebarIcon.textContent = '📊';
        if (sidebarText) sidebarText.textContent = 'Loading...';
        if (sidebarGoals) sidebarGoals.textContent = '0/0';
        if (sidebarBudget) sidebarBudget.textContent = '0%';
        if (sidebarActivity) sidebarActivity.textContent = '0';
    }
}

function updateFinancialStatus() {
    const statusElements = {
        emoji: document.getElementById('status-emoji'),
        message: document.getElementById('status-message'),
        icon: document.getElementById('status-icon'),
        sidebarIcon: document.getElementById('sidebar-status-icon'),
        sidebarText: document.getElementById('sidebar-status-text'),
        sidebarGoals: document.getElementById('sidebar-goals-completed'),
        sidebarBudget: document.getElementById('sidebar-budget-status'),
        sidebarActivity: document.getElementById('sidebar-recent-activity')
    };
    
    // Only proceed if we have the financial status API
    if (typeof loadFinancialStatus === 'function') {
        loadFinancialStatus();
    }
}

// Setup tooltips
function setupTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) + 'px';
            tooltip.style.top = rect.top - 40 + 'px';
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                document.body.removeChild(this._tooltip);
                this._tooltip = null;
            }
        });
    });
}

// Enhanced navigation functionality
function enhanceNavigation() {
    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.altKey) {
            switch(e.key) {
                case '1':
                    e.preventDefault();
                    window.location.href = '/';
                    break;
                case '2':
                    e.preventDefault();
                    window.location.href = '/goals';
                    break;
                case '3':
                    e.preventDefault();
                    window.location.href = '/budget';
                    break;
                case '4':
                    e.preventDefault();
                    window.location.href = '/journal';
                    break;
            }
        }
    });
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', () => {
    enhanceNavigation();
    
    // Add performance monitoring
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const loadTime = performance.now();
                if (loadTime > 3000) {
                    console.warn('Page load time is slow:', loadTime + 'ms');
                }
            }, 0);
        });
    }
});