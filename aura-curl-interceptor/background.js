// Background Service Worker - Manages extension icon based on checklist completion

console.log('%c[Background] Service Worker started', 'color: blue; font-weight: bold;');

// Initialize extension with red icon (incomplete state)
chrome.runtime.onInstalled.addListener(() => {
  console.log('%c[Background] Extension installed/updated - Setting red icon', 'color: blue;');
  setRedIcon();

  // Initialize checklist state
  chrome.storage.local.set({
    checklistState: {
      header: false,
      workOrdersList: false,
      piiDetails: false
    }
  });
});

// Listen for storage changes to update icon and show notifications
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.checklistState) {
    const state = changes.checklistState.newValue;
    console.log('%c[Background] Checklist state changed:', 'color: blue;', state);
    updateIcon(state);
  }

  // Show notification when new request is captured
  if (area === 'local' && changes.auraRequests) {
    const newRequests = changes.auraRequests.newValue || [];
    const oldRequests = changes.auraRequests.oldValue || [];

    // Check if a new request was added
    if (newRequests.length > oldRequests.length) {
      const newRequest = newRequests[0]; // Most recent is first
      showNotification(newRequest);
    }
  }
});

// Update icon based on checklist completion
function updateIcon(state) {
  const allComplete = state.header && state.workOrdersList && state.piiDetails;

  if (allComplete) {
    console.log('%c[Background] ✅ All 3 interceptors captured - Setting GREEN icon', 'color: green; font-weight: bold;');
    setGreenIcon();
  } else {
    console.log('%c[Background] ❌ Interceptors incomplete - Setting RED icon', 'color: red; font-weight: bold;');
    setRedIcon();
  }
}

// Set red icon (incomplete)
function setRedIcon() {
  chrome.action.setIcon({
    path: {
      '16': 'icons/icon16-red.png',
      '48': 'icons/icon48-red.png',
      '128': 'icons/icon128-red.png'
    }
  }).catch(err => console.error('[Background] Error setting red icon:', err));
}

// Set green icon (complete)
function setGreenIcon() {
  chrome.action.setIcon({
    path: {
      '16': 'icons/icon16-green.png',
      '48': 'icons/icon48-green.png',
      '128': 'icons/icon128-green.png'
    }
  }).catch(err => console.error('[Background] Error setting green icon:', err));
}

// Show notification when request is intercepted
function showNotification(request) {
  const requestName = request.name || 'Aura Request';
  const timestamp = new Date(request.timestamp).toLocaleTimeString();

  // Determine icon and message based on request type
  let iconPath = 'icons/icon128.png';
  let title = '';
  let message = '';

  if (request.name === 'HEADER') {
    iconPath = 'icons/icon128-green.png';
    title = '🎯 HEADER Intercepted!';
    message = `Technician Work Order List View captured at ${timestamp}`;
  } else if (request.name === 'Work Orders List') {
    iconPath = 'icons/icon128-blue.png';
    title = '📋 Work Orders List Intercepted!';
    message = `RecordGvp.getRecord request captured at ${timestamp}`;
  } else if (request.name === 'PII Details') {
    iconPath = 'icons/icon128-orange.png';
    title = '🔶 PII Details Intercepted!';
    message = `PII Work Order Details captured at ${timestamp}`;
  } else {
    title = `✅ ${requestName} Intercepted!`;
    message = `Request captured at ${timestamp}`;
  }

  console.log('%c[Background] Showing notification:', 'color: blue;', title);

  chrome.notifications.create({
    type: 'basic',
    iconUrl: iconPath,
    title: title,
    message: message,
    priority: 2,
    requireInteraction: false
  }).then(notificationId => {
    console.log('%c[Background] ✓ Notification shown:', 'color: green;', notificationId);

    // Auto-close notification after 5 seconds
    setTimeout(() => {
      chrome.notifications.clear(notificationId);
    }, 5000);
  }).catch(err => {
    console.error('%c[Background] Error showing notification:', 'color: red;', err);
  });
}

// Message handler for manual icon updates
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'updateChecklistState') {
    console.log('%c[Background] Received updateChecklistState message:', 'color: blue;', message.state);
    updateIcon(message.state);
    sendResponse({ success: true });
  }
  return true;
});

console.log('%c[Background] Service Worker ready', 'color: green; font-weight: bold;');
