// Application state
let savedCookie = '';
let requests = [];
let selectedRequestIndex = -1;
let serverUrl = '';
let autoUpdateEnabled = false;

console.log('%c[Popup] ===== POPUP STARTED ===== ', 'color: white; background: blue; font-weight: bold; padding: 5px 10px;');

// ========================================
// TAB SYSTEM
// ========================================
function setupTabs() {
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.dataset.tab;

      // Remove active from all tabs and contents
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      // Add active to clicked tab and corresponding content
      tab.classList.add('active');
      document.getElementById('tab-' + targetTab).classList.add('active');
    });
  });
}

// ========================================
// ACCORDION SYSTEM
// ========================================
function setupAccordions() {
  const accordionHeaders = document.querySelectorAll('.accordion-header');

  accordionHeaders.forEach(header => {
    header.addEventListener('click', () => {
      const accordion = header.parentElement;
      const wasActive = accordion.classList.contains('active');

      // Toggle accordion
      accordion.classList.toggle('active');

      // Update arrow
      const arrow = header.querySelector('.accordion-arrow');
      arrow.textContent = wasActive ? '▶' : '▼';

      console.log(`%c[Popup] Accordion toggled: ${wasActive ? 'closed' : 'opened'}`, 'color: blue;');
    });
  });
}

// Legacy function for compatibility (if needed elsewhere)
function toggleAccordion(header) {
  const accordion = header.parentElement;
  const wasActive = accordion.classList.contains('active');

  // Toggle accordion
  accordion.classList.toggle('active');

  // Update arrow
  const arrow = header.querySelector('.accordion-arrow');
  arrow.textContent = wasActive ? '▶' : '▼';
}

// ========================================
// CURL MODAL
// ========================================
function openCurlModal(curlContent) {
  const modal = document.getElementById('curl-modal');
  const curlElement = document.getElementById('curl-content');

  curlElement.textContent = curlContent;
  modal.classList.add('active');
}

function closeCurlModal() {
  const modal = document.getElementById('curl-modal');
  modal.classList.remove('active');
}

// ========================================
// STATUS BAR UPDATE (Real-time)
// ========================================
function updateStatusBar() {
  // Update Cookies status
  const cookiesChip = document.getElementById('status-cookies');
  if (savedCookie) {
    cookiesChip.classList.add('active');
    cookiesChip.querySelector('.status-icon').textContent = '🟢';
  } else {
    cookiesChip.classList.remove('active');
    cookiesChip.querySelector('.status-icon').textContent = '🔴';
  }

  // Update Server status
  const serverChip = document.getElementById('status-server');
  if (serverUrl) {
    serverChip.classList.add('active');
    serverChip.querySelector('.status-icon').textContent = '🟢';
  } else {
    serverChip.classList.remove('active');
    serverChip.querySelector('.status-icon').textContent = '🔴';
  }

  // Update Interceptor status (always assume active if cookies are set)
  const interceptorChip = document.getElementById('status-interceptor');
  if (savedCookie) {
    interceptorChip.classList.add('active');
    interceptorChip.querySelector('.status-icon').textContent = '⚡';
  } else {
    interceptorChip.classList.remove('active');
    interceptorChip.querySelector('.status-icon').textContent = '❌';
  }

  // Update Auto-sync status
  const autosyncChip = document.getElementById('status-autosync');
  if (autoUpdateEnabled) {
    autosyncChip.classList.add('active');
    autosyncChip.querySelector('.status-icon').textContent = '🔄';
  } else {
    autosyncChip.classList.remove('active');
    autosyncChip.querySelector('.status-icon').textContent = '⛔';
  }

  // Update accordion statuses in Config tab
  updateAccordionStatuses();
}

// ========================================
// ACCORDION STATUS UPDATE
// ========================================
function updateAccordionStatuses() {
  // Update Cookie accordion status
  const cookieStatus = document.getElementById('acc-cookie-status');
  if (savedCookie) {
    cookieStatus.textContent = '✓ Configured';
    cookieStatus.classList.add('active');
  } else {
    cookieStatus.textContent = 'Not configured';
    cookieStatus.classList.remove('active');
  }

  // Update Server accordion status
  const serverStatus = document.getElementById('acc-server-status');
  if (serverUrl) {
    serverStatus.textContent = '✓ Configured';
    serverStatus.classList.add('active');
  } else {
    serverStatus.textContent = 'Not configured';
    serverStatus.classList.remove('active');
  }

  // Update Auto-sync accordion status
  const autosyncStatus = document.getElementById('acc-autosync-status');
  if (autoUpdateEnabled) {
    autosyncStatus.textContent = '✓ Enabled';
    autosyncStatus.classList.add('active');
  } else {
    autosyncStatus.textContent = 'Disabled';
    autosyncStatus.classList.remove('active');
  }
}

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  console.log('%c[Popup] DOMContentLoaded - Initializing...', 'color: blue;');

  // Load saved cookie and server config
  console.log('%c[Popup] Loading data from storage...', 'color: blue;');
  const data = await chrome.storage.local.get(['auraCookie', 'auraRequests', 'checklistState', 'serverUrl', 'autoUpdateEnabled']);
  console.log('%c[Popup] Data loaded:', 'color: blue;', {
    hasCookie: !!data.auraCookie,
    requestCount: data.auraRequests?.length || 0,
    checklistState: data.checklistState,
    serverUrl: data.serverUrl,
    autoUpdateEnabled: data.autoUpdateEnabled
  });

  if (data.auraCookie) {
    savedCookie = data.auraCookie;
    document.getElementById('cookie-input').value = savedCookie;
    console.log('%c[Popup] ✓ Cookie loaded', 'color: green;');
  } else {
    console.log('%c[Popup] No saved cookie', 'color: orange;');
  }

  // Load server configuration
  if (data.serverUrl) {
    serverUrl = data.serverUrl;
    document.getElementById('server-url').value = serverUrl;
    console.log('%c[Popup] ✓ Server URL loaded:', 'color: green;', serverUrl);
  } else {
    document.getElementById('server-url').value = 'http://localhost:8080';
    console.log('%c[Popup] No saved server URL, using default', 'color: orange;');
  }

  if (data.autoUpdateEnabled !== undefined) {
    autoUpdateEnabled = data.autoUpdateEnabled;
    document.getElementById('auto-update-enabled').checked = autoUpdateEnabled;
    console.log('%c[Popup] ✓ Auto-update enabled:', 'color: green;', autoUpdateEnabled);
  }

  if (data.auraRequests && data.auraRequests.length > 0) {
    requests = data.auraRequests;
    renderRequests();
    updateRequestCount();
    updateChecklist(requests);
    console.log('%c[Popup] ✓ Requests loaded:', 'color: green;', requests.length);
  } else {
    console.log('%c[Popup] No saved requests', 'color: orange;');
  }

  // Initialize checklist state if it doesn't exist
  if (!data.checklistState) {
    await chrome.storage.local.set({
      checklistState: {
        header: false,
        workOrdersList: false,
        piiDetails: false
      }
    });
  } else {
    renderChecklist(data.checklistState);
  }

  // Setup tabs system
  setupTabs();
  console.log('%c[Popup] ✓ Tabs system initialized', 'color: green;');

  // Setup accordions system
  setupAccordions();
  console.log('%c[Popup] ✓ Accordions system initialized', 'color: green;');

  // Update status bar with loaded data
  updateStatusBar();
  console.log('%c[Popup] ✓ Status bar updated', 'color: green;');

  // Event listeners
  console.log('%c[Popup] Installing event listeners...', 'color: blue;');
  document.getElementById('save-cookie').addEventListener('click', saveCookie);
  document.getElementById('inject-interceptor').addEventListener('click', injectInterceptor);
  document.getElementById('copy-curl-modal').addEventListener('click', copyCurl);
  document.getElementById('clear-all-btn').addEventListener('click', clearAll);
  document.getElementById('save-server-config').addEventListener('click', saveServerConfig);
  document.getElementById('sync-all-btn').addEventListener('click', syncAllToPython);
  document.getElementById('open-viewer-btn').addEventListener('click', openViewer);

  // Auto-update checkbox listener
  document.getElementById('auto-update-enabled').addEventListener('change', async (e) => {
    autoUpdateEnabled = e.target.checked;
    await chrome.storage.local.set({ autoUpdateEnabled });
    updateStatusBar();
    console.log('%c[Popup] ✓ Auto-update toggled:', 'color: green;', autoUpdateEnabled);
  });

  console.log('%c[Popup] ✓ Event listeners installed', 'color: green;');

  // Listen for new requests
  console.log('%c[Popup] Installing storage change listener...', 'color: blue;');
  chrome.storage.onChanged.addListener(async (changes, area) => {
    console.log('%c[Popup] Storage changed!', 'color: blue;', { area, changes });

    if (area === 'local' && changes.auraRequests) {
      console.log('%c[Popup] ✓ New requests detected:', 'color: green;', changes.auraRequests.newValue?.length || 0);
      const oldRequests = changes.auraRequests.oldValue || [];
      const newRequests = changes.auraRequests.newValue || [];

      requests = newRequests;
      renderRequests();
      updateRequestCount();
      updateChecklist(requests);

      // Check if a new request was added and auto-update is enabled
      if (newRequests.length > oldRequests.length && autoUpdateEnabled) {
        const newRequest = newRequests[0]; // Most recent is first
        console.log('%c[Popup] 🤖 Auto-updating credentials for:', 'color: blue; font-weight: bold;', newRequest.name);
        await autoUpdateCredentials(newRequest);
      }
    }

    if (area === 'local' && changes.checklistState) {
      console.log('%c[Popup] ✓ Checklist state updated:', 'color: green;', changes.checklistState.newValue);
      renderChecklist(changes.checklistState.newValue);
    }
  });
  console.log('%c[Popup] ✓ Storage listener installed', 'color: green;');

  console.log('%c[Popup] ===== POPUP READY ===== ', 'color: white; background: green; font-weight: bold; padding: 5px 10px;');
});

// Save cookie
async function saveCookie() {
  console.log('%c[Popup] Saving cookie...', 'color: blue;');
  const cookieInput = document.getElementById('cookie-input');
  const cookie = cookieInput.value.trim();

  console.log('%c[Popup] Cookie length:', 'color: blue;', cookie.length);

  if (!cookie) {
    console.log('%c[Popup] ❌ Empty cookie', 'color: red;');
    showToast('Please enter a valid cookie', 'error');
    return;
  }

  savedCookie = cookie;
  await chrome.storage.local.set({ auraCookie: cookie });
  updateStatusBar();
  console.log('%c[Popup] ✓ Cookie saved to storage', 'color: green;');

  // If there are intercepted requests, update their cURL with the new cookie
  if (requests.length > 0) {
    console.log('%c[Popup] Updating cURL for existing requests...', 'color: blue;');

    // If a request is currently selected, regenerate its cURL with the new cookie
    if (selectedRequestIndex !== -1) {
      const request = requests[selectedRequestIndex];
      const curl = generateCurl(request, cookie);
      document.getElementById('curl-content').textContent = curl;
      console.log('%c[Popup] ✓ cURL updated for selected request', 'color: green;');
    }

    showToast(`Cookie saved! ${requests.length} request(s) will use the new cookie`);
  } else {
    showToast('Cookie saved successfully');
  }
}

// Inject interceptor manually
async function injectInterceptor() {
  console.log('%c[Popup] ===== INJECTING INTERCEPTOR MANUALLY =====', 'color: white; background: blue; font-weight: bold; padding: 5px;');

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  console.log('%c[Popup] Current tab:', 'color: blue;', { id: tab?.id, url: tab?.url });

  if (!tab || !tab.id) {
    console.log('%c[Popup] ❌ No active tab', 'color: red;');
    showToast('Could not detect active tab', 'error');
    return;
  }

  // Verify we're on a valid URL
  if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
    console.log('%c[Popup] ❌ Cannot inject on Chrome pages', 'color: red;');
    showToast('Cannot activate on Chrome internal pages', 'error');
    return;
  }

  try {
    console.log('%c[Popup] Injecting content.js on tab:', 'color: blue;', tab.id);

    // Inject content script
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });

    console.log('%c[Popup] ✓✓✓ Content script injected successfully ✓✓✓', 'color: white; background: green; font-weight: bold; padding: 5px;');
    showToast('✓ Interceptor activated! Reload page (F5) and perform actions');

    // Show instructions
    console.log('%c[Popup] INSTRUCTIONS:', 'color: blue; font-weight: bold;');
    console.log('%c[Popup] 1. Reload the page (F5)', 'color: blue;');
    console.log('%c[Popup] 2. Open console (F12)', 'color: blue;');
    console.log('%c[Popup] 3. Look for [Aura Interceptor] logs', 'color: blue;');
    console.log('%c[Popup] 4. Perform actions in Salesforce', 'color: blue;');

  } catch (err) {
    console.error('%c[Popup] ❌❌❌ INJECTION ERROR:', 'color: white; background: red; font-weight: bold; padding: 5px;');
    console.error('%c[Popup] Error:', 'color: red;', err);
    console.error('%c[Popup] Message:', 'color: red;', err.message);

    if (err.message.includes('Cannot access')) {
      showToast('Error: No permissions for this page. Check chrome://extensions/', 'error');
    } else if (err.message.includes('Refused to execute')) {
      showToast('Script already loaded. Reload page (F5)', 'error');
    } else {
      showToast('Error: ' + err.message, 'error');
    }
  }
}

// Render requests list
function renderRequests() {
  console.log('%c[Popup] Rendering requests...', 'color: blue;', requests.length);
  const list = document.getElementById('requests-list');

  if (requests.length === 0) {
    console.log('%c[Popup] No requests to display', 'color: orange;');
    list.innerHTML = `
      <div class="empty-state">
        <p>⏳ Waiting for requests...</p>
        <small>Navigate to Salesforce page and perform an Aura request</small>
      </div>
    `;
    return;
  }

  console.log('%c[Popup] Rendering', 'color: green;', requests.length, 'requests');

  list.innerHTML = requests.map((req, index) => {
    const displayName = req.name || req.url;
    const isHeader = req.name === 'HEADER';
    const isWorkOrdersList = req.name === 'Work Orders List';
    const isPIIDetails = req.name === 'PII Details';

    let itemClass = '';
    let icon = '';

    if (isHeader) {
      itemClass = 'style="background: #d1fae5; border: 2px solid #10b981;"';
      icon = '🎯 ';
    } else if (isWorkOrdersList) {
      itemClass = 'style="background: #dbeafe; border: 2px solid #3b82f6;"';
      icon = '📋 ';
    } else if (isPIIDetails) {
      itemClass = 'style="background: #ffedd5; border: 2px solid #fb923c;"';
      icon = '🔶 ';
    }

    return `
      <div class="request-item ${index === selectedRequestIndex ? 'active' : ''}" data-index="${index}" ${itemClass}>
        <div class="request-item-header">
          <span class="request-method">${req.method}</span>
          <span class="request-time">${new Date(req.timestamp).toLocaleTimeString()}</span>
        </div>
        <div class="request-item-content">
          <div class="request-url">${icon}${displayName}</div>
          <button class="btn-copy-curl" data-index="${index}" title="Copy cURL">
            📋 Copy cURL
          </button>
        </div>
      </div>
    `;
  }).join('');

  // Event listeners para cada petición
  document.querySelectorAll('.request-item').forEach(item => {
    item.addEventListener('click', (e) => {
      // Don't select if clicking the copy button
      if (e.target.classList.contains('btn-copy-curl') || e.target.closest('.btn-copy-curl')) {
        return;
      }
      const index = parseInt(item.dataset.index);
      selectRequest(index);
    });
  });

  // Event listeners para botones de copiar cURL
  document.querySelectorAll('.btn-copy-curl').forEach(button => {
    button.addEventListener('click', async (e) => {
      e.stopPropagation(); // Prevent request selection
      const index = parseInt(button.dataset.index);
      await copyCurlFromRequest(index);
    });
  });
}

// Select request
async function selectRequest(index) {
  console.log('%c[Popup] Request selected:', 'color: blue;', index);
  selectedRequestIndex = index;
  const request = requests[index];

  // Actualizar UI
  document.querySelectorAll('.request-item').forEach(item => {
    item.classList.remove('active');
  });
  document.querySelector(`[data-index="${index}"]`)?.classList.add('active');

  // Get saved cookie
  const data = await chrome.storage.local.get(['auraCookie']);
  const cookie = data.auraCookie || '';

  if (!cookie) {
    showToast('Please save a cookie first', 'error');
    return;
  }

  // Generate and show cURL in modal
  const curl = generateCurl(request, cookie);
  openCurlModal(curl);
  console.log('%c[Popup] ✓ cURL modal opened', 'color: green;');
}

// Generate cURL command (WITH decoding - human-readable)
function generateCurl(request, cookie) {
  const { url, method, body, referer, userAgent, acceptLanguage } = request;

  function getRawPair(name) {
    const re = new RegExp(name.replace(".", "\\.") + "=[^&]*");
    const m = body.match(re);
    return m ? m[0] : null;
  }

  function decodeParameter(rawPair) {
    if (!rawPair) return null;
    const idx = rawPair.indexOf("=");
    if (idx === -1) return rawPair;

    const key = rawPair.slice(0, idx);
    const encodedValue = rawPair.slice(idx + 1);

    try {
      // Decode URL-encoded value
      const decodedValue = decodeURIComponent(encodedValue.replace(/\+/g, " "));
      return `${key}=${decodedValue}`;
    } catch (e) {
      // If decode fails, return as-is
      return rawPair;
    }
  }

  let lines = [];
  lines.push(`curl '${url}' \\`);
  lines.push(`  -X ${method} \\`);
  lines.push(`  -H 'Accept: application/json' \\`);
  lines.push(`  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \\`);
  lines.push(`  -H 'Origin: ${new URL(url).origin}' \\`);
  lines.push(`  -H 'Referer: ${referer}' \\`);
  lines.push(`  -H 'User-Agent: ${userAgent}' \\`);
  lines.push(`  -H 'Accept-Language: ${acceptLanguage}' \\`);
  lines.push(`  -H 'Cache-Control: no-cache' \\`);
  lines.push(`  -H 'Pragma: no-cache' \\`);
  lines.push(`  -H 'Cookie: ${cookie}' \\`);

  // Extract raw parameters and DECODE them
  const raw_message = getRawPair("message");
  const raw_context = getRawPair("aura.context");
  const raw_page = getRawPair("aura.pageURI");
  const raw_token = getRawPair("aura.token");

  if (raw_message) {
    // DECODE all parameters for human-readable output
    const decoded_message = decodeParameter(raw_message);
    const decoded_context = decodeParameter(raw_context);
    const decoded_page = decodeParameter(raw_page);
    const decoded_token = decodeParameter(raw_token);

    // message uses --data-raw (decoded, human-readable)
    lines.push(`  --data-raw '${decoded_message}' \\`);

    // aura.context, aura.pageURI, aura.token use --data-urlencode (curl will encode them)
    if (decoded_context) lines.push(`  --data-urlencode '${decoded_context}' \\`);
    if (decoded_page) lines.push(`  --data-urlencode '${decoded_page}' \\`);
    if (decoded_token) lines.push(`  --data-urlencode '${decoded_token}'`);
  } else {
    // For requests without standard parameters, use entire body as-is
    const escapedBody = body.replace(/'/g, "'\\''");
    lines.push(`  --data-raw '${escapedBody}'`);
  }

  return lines.join('\n');
}

// Copy cURL to clipboard
async function copyCurl() {
  const curl = document.getElementById('curl-content').textContent;

  try {
    await navigator.clipboard.writeText(curl);
    showToast('cURL copied to clipboard');
  } catch (err) {
    // Fallback for browsers without clipboard API support
    const textarea = document.createElement('textarea');
    textarea.value = curl;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('cURL copied to clipboard');
  }
}

// Copy cURL directly from request list
async function copyCurlFromRequest(index) {
  console.log('%c[Popup] Copying cURL from request:', 'color: blue;', index);
  const request = requests[index];

  // Get saved cookie
  const data = await chrome.storage.local.get(['auraCookie']);
  const cookie = data.auraCookie || '';

  if (!cookie) {
    showToast('Please save a cookie first', 'error');
    return;
  }

  // Generate cURL
  const curl = generateCurl(request, cookie);

  // Copy to clipboard
  try {
    await navigator.clipboard.writeText(curl);
    const requestName = request.name || 'Request';
    showToast(`✅ ${requestName} cURL copied!`);
    console.log('%c[Popup] ✓ cURL copied from list', 'color: green;');
  } catch (err) {
    // Fallback for browsers without clipboard API support
    const textarea = document.createElement('textarea');
    textarea.value = curl;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    const requestName = request.name || 'Request';
    showToast(`✅ ${requestName} cURL copied!`);
    console.log('%c[Popup] ✓ cURL copied from list (fallback)', 'color: green;');
  }
}

// Clear all
async function clearAll() {
  console.log('%c[Popup] Clear all clicked', 'color: blue;');
  if (confirm('Are you sure you want to clear all requests?')) {
    requests = [];
    selectedRequestIndex = -1;
    await chrome.storage.local.set({ auraRequests: [] });
    renderRequests();
    updateRequestCount();
    closeCurlModal(); // Close modal if it's open
    showToast('Requests cleared');
    console.log('%c[Popup] ✓ All requests cleared', 'color: green;');
  }
}

// Update request counter
function updateRequestCount() {
  document.getElementById('request-count').textContent = requests.length;
}

// Show toast notification
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3000);
}

// Update checklist based on captured requests
async function updateChecklist(requests) {
  console.log('%c[Popup] Updating checklist...', 'color: blue;', requests.length);

  const hasHeader = requests.some(req => req.name === 'HEADER');
  const hasWorkOrdersList = requests.some(req => req.name === 'Work Orders List');
  const hasPIIDetails = requests.some(req => req.name === 'PII Details');

  console.log('%c[Popup] Checklist status:', 'color: blue;', {
    hasHeader,
    hasWorkOrdersList,
    hasPIIDetails
  });

  const checklistState = {
    header: hasHeader,
    workOrdersList: hasWorkOrdersList,
    piiDetails: hasPIIDetails
  };

  // Save to storage
  await chrome.storage.local.set({ checklistState });

  // Update UI
  renderChecklist(checklistState);

  console.log('%c[Popup] ✓ Checklist updated', 'color: green;');
}

// Render checklist UI
function renderChecklist(state) {
  console.log('%c[Popup] Rendering checklist:', 'color: blue;', state);

  const headerCheck = document.getElementById('check-header');
  const workOrdersCheck = document.getElementById('check-work-orders');
  const piiDetailsCheck = document.getElementById('check-pii-details');

  // Update HEADER
  if (state.header) {
    headerCheck.classList.add('completed');
    headerCheck.querySelector('.checkbox').textContent = '✅';
  } else {
    headerCheck.classList.remove('completed');
    headerCheck.querySelector('.checkbox').textContent = '❌';
  }

  // Update Work Orders List
  if (state.workOrdersList) {
    workOrdersCheck.classList.add('completed');
    workOrdersCheck.querySelector('.checkbox').textContent = '✅';
  } else {
    workOrdersCheck.classList.remove('completed');
    workOrdersCheck.querySelector('.checkbox').textContent = '❌';
  }

  // Update PII Details
  if (state.piiDetails) {
    piiDetailsCheck.classList.add('completed');
    piiDetailsCheck.querySelector('.checkbox').textContent = '✅';
  } else {
    piiDetailsCheck.classList.remove('completed');
    piiDetailsCheck.querySelector('.checkbox').textContent = '❌';
  }

  console.log('%c[Popup] ✓ Checklist rendered', 'color: green;');
}

// Save server configuration
async function saveServerConfig() {
  console.log('%c[Popup] Saving server config...', 'color: blue;');
  const serverUrlInput = document.getElementById('server-url');
  const autoUpdateCheckbox = document.getElementById('auto-update-enabled');

  const url = serverUrlInput.value.trim();
  const autoUpdate = autoUpdateCheckbox.checked;

  if (!url) {
    showToast('Please enter a valid server URL', 'error');
    return;
  }

  // Validate URL format
  try {
    new URL(url);
  } catch (e) {
    showToast('Invalid URL format', 'error');
    return;
  }

  serverUrl = url;
  autoUpdateEnabled = autoUpdate;

  await chrome.storage.local.set({ serverUrl: url, autoUpdateEnabled: autoUpdate });
  updateStatusBar();

  console.log('%c[Popup] ✓ Server config saved:', 'color: green;', { url, autoUpdate });
  showToast(`✅ Server configured: ${autoUpdate ? 'Auto-update ENABLED' : 'Auto-update DISABLED'}`);
}

// Auto-update credentials to Python server
async function autoUpdateCredentials(request) {
  if (!serverUrl) {
    console.log('%c[Popup] ❌ Server URL not configured', 'color: orange;');
    return;
  }

  if (!request.name) {
    console.log('%c[Popup] ❌ Request has no name, skipping auto-update', 'color: orange;');
    return;
  }

  // Map request name to credential type
  const credentialTypeMap = {
    'HEADER': 'HEADER',
    'Work Orders List': 'FIRST',
    'PII Details': 'PII'
  };

  const credentialType = credentialTypeMap[request.name];

  if (!credentialType) {
    console.log('%c[Popup] ❌ Unknown request type:', 'color: orange;', request.name);
    return;
  }

  // Update sync status to "syncing"
  updateSyncStatus(request.name, 'syncing');

  try {
    console.log(`%c[Popup] 📤 Sending ${request.name} to Python server...`, 'color: blue; font-weight: bold;');

    // Get saved cookie
    const data = await chrome.storage.local.get(['auraCookie']);
    const cookie = data.auraCookie || '';

    if (!cookie) {
      console.log('%c[Popup] ❌ No cookie saved', 'color: red;');
      updateSyncStatus(request.name, 'error');
      showToast(`❌ ${request.name}: No cookie configured`, 'error');
      return;
    }

    // Generate cURL
    const curl = generateCurl(request, cookie);

    // Debug: Log the cURL being sent
    console.log('%c[Popup] 📤 Sending cURL to Python:', 'color: magenta; font-weight: bold;');
    console.log('%c[Popup] cURL length:', 'color: magenta;', curl.length);
    console.log('%c[Popup] cURL preview (first 500 chars):', 'color: magenta;', curl.substring(0, 500));

    // Extract and log the token from the cURL
    const tokenMatch = curl.match(/--data-urlencode 'aura\.token=([^']+)'/);
    if (tokenMatch) {
      console.log('%c[Popup] 🔑 Token being sent (first 100 chars):', 'color: magenta; font-weight: bold;', tokenMatch[1].substring(0, 100));
      console.log('%c[Popup] 🔑 Token being sent (last 50 chars):', 'color: magenta; font-weight: bold;', tokenMatch[1].slice(-50));
    } else {
      console.log('%c[Popup] ❌ No token found in cURL!', 'color: red; font-weight: bold;');
    }

    // Send to Python server
    const response = await fetch(`${serverUrl}/api/parse-request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        request_text: curl,
        credential_type: credentialType
      })
    });

    const result = await response.json();

    if (response.ok && result.success) {
      console.log(`%c[Popup] ✅ ${request.name} credentials parsed successfully`, 'color: green; font-weight: bold;');
      console.log(`%c[Popup] Extracted credentials:`, 'color: green;', result.credentials);

      // Now SAVE the credentials to .env file
      console.log(`%c[Popup] 💾 Saving credentials to .env file...`, 'color: blue; font-weight: bold;');

      const saveResponse = await fetch(`${serverUrl}/api/update-credentials`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          credentials: result.credentials
        })
      });

      const saveResult = await saveResponse.json();

      if (saveResponse.ok && saveResult.success) {
        console.log(`%c[Popup] ✅ ${request.name} credentials SAVED to .env successfully`, 'color: green; font-weight: bold;');
        updateSyncStatus(request.name, 'success');
        showToast(`✅ ${request.name} synced and saved to .env!`);
      } else {
        console.error(`%c[Popup] ❌ ${request.name} save failed:`, 'color: red;', saveResult.error || saveResult.message);
        updateSyncStatus(request.name, 'error');
        showToast(`❌ ${request.name}: Save failed - ${saveResult.error || saveResult.message}`, 'error');
      }
    } else {
      console.error(`%c[Popup] ❌ ${request.name} parse failed:`, 'color: red;', result.error || result.message);
      updateSyncStatus(request.name, 'error');
      showToast(`❌ ${request.name}: ${result.error || result.message}`, 'error');
    }

  } catch (error) {
    console.error(`%c[Popup] ❌ Error updating ${request.name}:`, 'color: red;', error);
    updateSyncStatus(request.name, 'error');
    showToast(`❌ ${request.name}: ${error.message}`, 'error');
  }
}

// Update sync status indicator
function updateSyncStatus(requestName, status) {
  const statusMap = {
    'HEADER': 'sync-header',
    'Work Orders List': 'sync-work-orders',
    'PII Details': 'sync-pii-details'
  };

  const elementId = statusMap[requestName];
  if (!elementId) return;

  const element = document.getElementById(elementId);
  if (!element) return;

  if (status === 'syncing') {
    element.textContent = '⏳ Syncing...';
    element.style.color = '#3b82f6'; // blue
  } else if (status === 'success') {
    element.textContent = '✅ Synced';
    element.style.color = '#10b981'; // green
  } else if (status === 'error') {
    element.textContent = '❌ Error';
    element.style.color = '#ef4444'; // red
  } else {
    element.textContent = '⏳';
    element.style.color = '#9ca3af'; // gray
  }
}

// Sync all captured requests to Python server
async function syncAllToPython() {
  console.log('%c[Popup] 🔄 Sync All to Python clicked', 'color: blue; font-weight: bold;');

  // Check if server is configured
  if (!serverUrl) {
    showToast('❌ Please configure Python server URL first', 'error');
    return;
  }

  // Check if cookie is configured
  const data = await chrome.storage.local.get(['auraCookie']);
  const cookie = data.auraCookie || '';

  if (!cookie) {
    showToast('❌ Please save a cookie first', 'error');
    return;
  }

  // Check if there are requests
  if (requests.length === 0) {
    showToast('❌ No requests to sync', 'error');
    return;
  }

  console.log(`%c[Popup] Starting sync of ${requests.length} requests...`, 'color: blue; font-weight: bold;');

  // Get the important requests (HEADER, Work Orders List, PII Details)
  const headerRequest = requests.find(req => req.name === 'HEADER');
  const workOrdersRequest = requests.find(req => req.name === 'Work Orders List');
  const piiDetailsRequest = requests.find(req => req.name === 'PII Details');

  const requestsToSync = [
    { request: headerRequest, name: 'HEADER' },
    { request: workOrdersRequest, name: 'Work Orders List' },
    { request: piiDetailsRequest, name: 'PII Details' }
  ].filter(item => item.request); // Filter out undefined requests

  if (requestsToSync.length === 0) {
    showToast('❌ No HEADER, Work Orders List, or PII Details requests found', 'error');
    return;
  }

  // Disable button during sync
  const syncBtn = document.getElementById('sync-all-btn');
  syncBtn.disabled = true;
  syncBtn.textContent = '⏳ Syncing...';
  syncBtn.style.opacity = '0.6';

  let successCount = 0;
  let errorCount = 0;

  // Sync each request
  for (const { request, name } of requestsToSync) {
    console.log(`%c[Popup] 📤 Syncing ${name}...`, 'color: blue; font-weight: bold;');
    updateSyncStatus(name, 'syncing');

    try {
      await autoUpdateCredentials(request);
      successCount++;
      console.log(`%c[Popup] ✅ ${name} synced successfully`, 'color: green; font-weight: bold;');
    } catch (error) {
      errorCount++;
      console.error(`%c[Popup] ❌ ${name} sync failed:`, 'color: red;', error);
      updateSyncStatus(name, 'error');
    }

    // Small delay between requests
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  // Re-enable button
  syncBtn.disabled = false;
  syncBtn.textContent = '🔄 Sync All to Python';
  syncBtn.style.opacity = '1';

  // Show summary
  if (errorCount === 0) {
    console.log(`%c[Popup] ✅ All ${successCount} requests synced successfully!`, 'color: green; font-weight: bold;');
    showToast(`✅ All ${successCount} requests synced to Python!`);
  } else {
    console.log(`%c[Popup] ⚠️ Sync completed with errors: ${successCount} success, ${errorCount} errors`, 'color: orange; font-weight: bold;');
    showToast(`⚠️ ${successCount} synced, ${errorCount} errors`, 'error');
  }
}

// ========================================
// OPEN VIEWER IN NEW TAB
// ========================================
async function openViewer() {
  console.log('%c[Popup] 📊 Open Viewer clicked', 'color: blue; font-weight: bold;');

  // Get server URL from storage
  const data = await chrome.storage.local.get(['serverUrl']);
  const url = data.serverUrl || 'http://localhost:8080';

  // Construct viewer URL
  const viewerUrl = url.endsWith('/') ? `${url}viewer` : `${url}/viewer`;

  console.log(`%c[Popup] Opening viewer at: ${viewerUrl}`, 'color: blue;');

  // Open viewer in new tab
  chrome.tabs.create({ url: viewerUrl });

  showToast('📊 Opening viewer in new tab...', 'success');
}
