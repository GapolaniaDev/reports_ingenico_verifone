// Content Script - Injects the interceptor into the page context
(function () {
  console.log('%c[Content Script] Injecting interceptor into page...', 'color: blue; font-weight: bold;');

  // Inject the script into the page context (not isolated)
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL('injected.js');
  script.onload = function() {
    console.log('%c[Content Script] ✓ Interceptor injected in page context', 'color: green; font-weight: bold;');
    this.remove();
  };
  script.onerror = function() {
    console.error('%c[Content Script] ❌ Error injecting script', 'color: red; font-weight: bold;');
  };
  (document.head || document.documentElement).appendChild(script);

  // Listen for events from injected script
  console.log('%c[Content Script] Listening for request events...', 'color: blue;');

  window.addEventListener('aura-interceptor-request', async (event) => {
    const { request, replaceAll } = event.detail;
    console.log('%c[Content Script] ✓ Request received from injected script', 'color: green;', request.name || request.url);

    try {
      let requests;

      if (replaceAll) {
        // If it's HEADER, replace ALL with just this record
        console.log('%c[Content Script] ⚡ HEADER detected - Replacing all records', 'color: yellow; font-weight: bold;');
        requests = [request];
      } else if (request.name === 'Work Orders List') {
        // For Work Orders List, keep only the most recent one
        console.log('%c[Content Script] 📋 Work Orders List detected - Keeping only most recent', 'color: blue; font-weight: bold;');
        const data = await chrome.storage.local.get(['auraRequests']);
        requests = data.auraRequests || [];

        // Remove any previous Work Orders List entries
        requests = requests.filter(req => req.name !== 'Work Orders List');

        // Add the new one at the beginning
        requests.unshift(request);
      } else if (request.name === 'PII Details') {
        // For PII Details, keep only the most recent one
        console.log('%c[Content Script] 🔶 PII Details detected - Keeping only most recent', 'color: orange; font-weight: bold;');
        const data = await chrome.storage.local.get(['auraRequests']);
        requests = data.auraRequests || [];

        // Remove any previous PII Details entries
        requests = requests.filter(req => req.name !== 'PII Details');

        // Add the new one at the beginning
        requests.unshift(request);
      } else {
        // Normal behavior for other requests
        const data = await chrome.storage.local.get(['auraRequests']);
        requests = data.auraRequests || [];
        requests.unshift(request);

        if (requests.length > 20) {
          requests.length = 20;
        }
      }

      await chrome.storage.local.set({ auraRequests: requests });
      console.log('%c[Content Script] ✓ Request saved to storage', 'color: green;', {
        name: request.name,
        total: requests.length
      });

      // Update checklist state
      await updateChecklistState(requests);
    } catch (error) {
      console.error('%c[Content Script] ❌ Error saving request:', 'color: red;', error);
    }
  });

  // Update checklist state based on captured requests
  async function updateChecklistState(requests) {
    const hasHeader = requests.some(req => req.name === 'HEADER');
    const hasWorkOrdersList = requests.some(req => req.name === 'Work Orders List');
    const hasPIIDetails = requests.some(req => req.name === 'PII Details');

    const checklistState = {
      header: hasHeader,
      workOrdersList: hasWorkOrdersList,
      piiDetails: hasPIIDetails
    };

    console.log('%c[Content Script] Updating checklist state:', 'color: blue;', checklistState);

    await chrome.storage.local.set({ checklistState });

    console.log('%c[Content Script] ✓ Checklist state updated', 'color: green;');
  }

  console.log('%c[Content Script] ===== READY =====', 'color: green; font-weight: bold;');

  // Old functions are no longer needed, injected.js does the work
  // But I'll leave them commented just in case

  function extractListViewFromMessage(messagePair) {
    console.log('%c[Aura Interceptor] Extracting listView from message...', 'color: #667eea;');
    try {
      const idx = messagePair.indexOf("=");
      const encoded = messagePair.slice(idx + 1);
      const jsonStr = decodeURIComponent(encoded.replace(/\+/g, " "));
      console.log('%c[Aura Interceptor] Message JSON (first 200 chars):', 'color: #667eea;', jsonStr.substring(0, 200));
      const obj = JSON.parse(jsonStr);
      const listView = obj?.actions?.[0]?.params?.listReference?.listViewIdOrName || null;
      console.log('%c[Aura Interceptor] ListView found:', 'color: #667eea;', listView);
      return listView;
    } catch (e) {
      console.error('%c[Aura Interceptor] Error extracting listView:', 'color: red;', e);
      return null;
    }
  }

  async function captureRequest(rawUrl, method, body) {
    console.log('%c[Aura Interceptor] ───── New request detected ─────', 'color: blue; font-weight: bold;');
    console.log('%c[Aura Interceptor] URL:', 'color: blue;', rawUrl);
    console.log('%c[Aura Interceptor] Method:', 'color: blue;', method);
    console.log('%c[Aura Interceptor] Body type:', 'color: blue;', typeof body);

    if (typeof body !== "string") {
      console.log('%c[Aura Interceptor] ❌ Body is not string, ignoring', 'color: orange;');
      return;
    }

    const url = rawUrl.startsWith("http") ? rawUrl : location.origin + rawUrl;
    console.log('%c[Aura Interceptor] Complete URL:', 'color: blue;', url);

    // Only capture Aura requests (both /s/sfsites/aura AND /aura for iframe requests)
    if (!url.includes("/s/sfsites/aura") && !url.includes("/aura?")) {
      console.log('%c[Aura Interceptor] ❌ Not an Aura request, ignoring', 'color: orange;');
      return;
    }

    console.log('%c[Aura Interceptor] ✓ Aura request detected', 'color: green;');

    function getRawPair(name) {
      const re = new RegExp(name.replace(".", "\\.") + "=[^&]*");
      const m = body.match(re);
      return m ? m[0] : null;
    }

    const raw_message = getRawPair("message");
    console.log('%c[Aura Interceptor] raw_message:', 'color: blue;', raw_message ? 'Found' : 'NOT FOUND');

    // ============================================================
    // FILTERS DISABLED - CAPTURING ALL AURA REQUESTS
    // ============================================================
    // if (!raw_message) {
    //   console.log('%c[Aura Interceptor] ❌ "message" parameter not found, ignoring', 'color: orange;');
    //   console.log('%c[Aura Interceptor] Body (first 500 chars):', 'color: orange;', body.substring(0, 500));
    //   return;
    // }
    //
    // console.log('%c[Aura Interceptor] ✓ Message parameter found', 'color: green;');
    //
    // // Filter only Technician_Work_Order_List_View requests
    // const listView = extractListViewFromMessage(raw_message);
    // console.log('%c[Aura Interceptor] Checking listView...', 'color: blue;');
    //
    // if (listView !== "Technician_Work_Order_List_View") {
    //   console.log('%c[Aura Interceptor] ❌ ListView does not match:', 'color: orange;', listView, '!== "Technician_Work_Order_List_View"');
    //   console.log('%c[Aura Interceptor] Request ignored by listView filter', 'color: orange;');
    //   return;
    // }
    // ============================================================

    console.log('%c[Aura Interceptor] ✓✓✓ VALID REQUEST (NO FILTERS) ✓✓✓', 'color: white; background: green; font-weight: bold; padding: 5px 10px;');
    console.log('%c[Aura Interceptor] Capturing ALL Aura requests', 'color: green; font-weight: bold;');
    console.log('%c[Aura Interceptor] Preparing to save...', 'color: blue;');

    // Create request object
    const request = {
      url: url,
      method: method || "POST",
      body: body,
      referer: location.href,
      userAgent: navigator.userAgent,
      acceptLanguage: navigator.languages?.join(",") || navigator.language || "",
      timestamp: Date.now()
    };

    console.log('%c[Aura Interceptor] Request object created:', 'color: blue;', {
      url: request.url,
      method: request.method,
      bodyLength: request.body.length,
      timestamp: new Date(request.timestamp).toISOString()
    });

    // Save to storage
    try {
      console.log('%c[Aura Interceptor] Accessing chrome.storage...', 'color: blue;');
      const data = await chrome.storage.local.get(['auraRequests']);
      console.log('%c[Aura Interceptor] Storage data retrieved:', 'color: blue;', data);

      const requests = data.auraRequests || [];
      console.log('%c[Aura Interceptor] Existing requests:', 'color: blue;', requests.length);

      // Add new request at the beginning (most recent first)
      requests.unshift(request);

      // Limit to last 20 requests
      if (requests.length > 20) {
        requests.length = 20;
      }

      console.log('%c[Aura Interceptor] Saving to storage...', 'color: blue;', requests.length, 'total requests');
      await chrome.storage.local.set({ auraRequests: requests });
      console.log('%c[Aura Interceptor] ✓✓✓ REQUEST SAVED SUCCESSFULLY ✓✓✓', 'color: white; background: green; font-weight: bold; padding: 5px 10px;');
      console.log('%c[Aura Interceptor] Total requests in storage:', 'color: green;', requests.length);
    } catch (error) {
      console.error('%c[Aura Interceptor] ❌❌❌ SAVE ERROR ❌❌❌', 'color: white; background: red; font-weight: bold; padding: 5px 10px;');
      console.error('[Aura Interceptor] Error details:', error);
      console.error('[Aura Interceptor] Error stack:', error.stack);
    }
  }

  // Intercept fetch more aggressively
  console.log('%c[Aura Interceptor] Installing fetch hook...', 'color: blue;');

  if (typeof window.fetch === 'function') {
    const origFetch = window.fetch;

    window.fetch = function (input, init = {}) {
      console.log('%c[Aura Interceptor] [FETCH] ===== FETCH CALLED ===== ', 'color: purple; font-weight: bold;');

      try {
        const rawUrl = typeof input === "string" ? input : input?.url;
        const method = init?.method || "GET";
        const body = init?.body;

        console.log('%c[Aura Interceptor] [FETCH] URL:', 'color: purple;', rawUrl);
        console.log('%c[Aura Interceptor] [FETCH] Method:', 'color: purple;', method);
        console.log('%c[Aura Interceptor] [FETCH] Body type:', 'color: purple;', typeof body);

        if (rawUrl && (rawUrl.includes("/s/sfsites/aura") || rawUrl.includes("/aura?"))) {
          console.log('%c[Aura Interceptor] [FETCH] ✓ AURA REQUEST!', 'color: green; font-weight: bold;');

          if (method.toUpperCase() === "POST" && typeof body === "string") {
            console.log('%c[Aura Interceptor] [FETCH] ✓ POST with string body, capturing...', 'color: green;');
            captureRequest(rawUrl, method, body);
          } else {
            console.log('%c[Aura Interceptor] [FETCH] Method or body do not match:', 'color: orange;', {
              method,
              bodyType: typeof body
            });
          }
        }
      } catch (err) {
        console.error('%c[Aura Interceptor] [FETCH] Error:', 'color: red;', err);
      }
      return origFetch.apply(this, arguments);
    };

    console.log('%c[Aura Interceptor] ✓ Fetch hook installed on window.fetch', 'color: green;');
  } else {
    console.log('%c[Aura Interceptor] ⚠️ window.fetch does not exist!', 'color: orange;');
  }

  // Intercept XMLHttpRequest more aggressively
  console.log('%c[Aura Interceptor] Installing XMLHttpRequest hook...', 'color: blue;');

  if (typeof XMLHttpRequest !== 'undefined') {
    const origOpen = XMLHttpRequest.prototype.open;
    const origSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url) {
      this._url = url;
      this._method = method;
      console.log('%c[Aura Interceptor] [XHR] ===== XHR.open() CALLED ===== ', 'color: purple; font-weight: bold;');
      console.log('%c[Aura Interceptor] [XHR] Method:', 'color: purple;', method);
      console.log('%c[Aura Interceptor] [XHR] URL:', 'color: purple;', url);
      return origOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function (body) {
      console.log('%c[Aura Interceptor] [XHR] ===== XHR.send() CALLED ===== ', 'color: purple; font-weight: bold;');
      console.log('%c[Aura Interceptor] [XHR] URL:', 'color: purple;', this._url);
      console.log('%c[Aura Interceptor] [XHR] Body type:', 'color: purple;', typeof body);

      try {
        if (this._url && (this._url.includes("/s/sfsites/aura") || this._url.includes("/aura?"))) {
          console.log('%c[Aura Interceptor] [XHR] ✓ AURA REQUEST!', 'color: green; font-weight: bold;');

          if (this._method?.toUpperCase() === "POST" && typeof body === "string") {
            console.log('%c[Aura Interceptor] [XHR] ✓ POST with string body, capturing...', 'color: green;');
            captureRequest(this._url, this._method, body);
          } else {
            console.log('%c[Aura Interceptor] [XHR] Method or body do not match:', 'color: orange;', {
              method: this._method,
              bodyType: typeof body
            });
          }
        }
      } catch (err) {
        console.error('%c[Aura Interceptor] [XHR] Error:', 'color: red;', err);
      }
      return origSend.apply(this, arguments);
    };

    console.log('%c[Aura Interceptor] ✓ XMLHttpRequest.prototype hook installed', 'color: green;');
  } else {
    console.log('%c[Aura Interceptor] ⚠️ XMLHttpRequest does not exist!', 'color: orange;');
  }

  console.log('%c[Aura Interceptor] ========== HOOKS INSTALLED ========== ', 'color: white; background: green; font-weight: bold; padding: 5px 10px;');
  console.log('%c[Aura Interceptor] Extension is ready. Make requests to see them captured.', 'color: green; font-weight: bold;');
  console.log('%c[Aura Interceptor] Open the extension popup to view saved requests.', 'color: green;');
})();
