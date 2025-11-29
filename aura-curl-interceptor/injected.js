// This script is injected DIRECTLY into the page (not as an isolated content script)
(function () {
  const isIframe = window !== window.top;
  const frameInfo = isIframe ? '[IFRAME]' : '[TOP WINDOW]';

  console.log(`%c[Aura Interceptor INJECTED] ===== STARTED ===== ${frameInfo}`, 'color: white; background: green; font-weight: bold; padding: 5px 10px;');
  console.log('%c[Aura Interceptor] Version: 2.0.0 (Injected in Page Context)', 'color: green;');
  console.log(`%c[Aura Interceptor] Running in: ${frameInfo}`, 'color: green; font-weight: bold;');
  console.log('%c[Aura Interceptor] Current URL:', 'color: green;', location.href);

  // List of captured requests (temporary)
  let capturedRequests = [];

  function decodePair(pair) {
    if (!pair) return "";
    const idx = pair.indexOf("=");
    if (idx === -1) return pair;

    const key = pair.slice(0, idx);
    const value = pair.slice(idx + 1);

    try {
      const decoded = decodeURIComponent(value.replace(/\+/g, " "));
      return `${key}=${decoded}`;
    } catch {
      return pair;
    }
  }

  function extractListViewFromMessage(messagePair) {
    try {
      const idx = messagePair.indexOf("=");
      const encoded = messagePair.slice(idx + 1);
      const jsonStr = decodeURIComponent(encoded.replace(/\+/g, " "));
      const obj = JSON.parse(jsonStr);
      return obj?.actions?.[0]?.params?.listReference?.listViewIdOrName || null;
    } catch {
      return null;
    }
  }

  function getRawPair(name, body) {
    const re = new RegExp(name.replace(".", "\\.") + "=[^&]*");
    const m = body.match(re);
    return m ? m[0] : null;
  }

  function buildCurlAndStore(rawUrl, method, body) {
    if (typeof body !== "string") {
      console.log('%c[Aura Interceptor] Body is not string, ignoring', 'color: orange;');
      return;
    }

    const origin = location.origin;
    const url = rawUrl.startsWith("http") ? rawUrl : origin + rawUrl;

    // Accept both /s/sfsites/aura AND /aura (for iframe requests)
    if (!url.includes("/s/sfsites/aura") && !url.includes("/aura?")) {
      console.log('%c[Aura Interceptor] Not an Aura request, ignoring', 'color: gray;');
      return;
    }

    const isIframe = window !== window.top;
    const frameInfo = isIframe ? '[IFRAME]' : '[TOP]';
    console.log(`%c[Aura Interceptor] ✓ Aura request detected ${frameInfo}`, 'color: blue; font-weight: bold;');

    // ============================================================
    // CHECK 1: PII Work Order Details (flowDevName in body)
    // ============================================================
    if (url.includes("aura.FlowRuntimeConnect.startFlow=1") &&
        body.includes("PII_Display_Work_Order_Details_Screen")) {
      console.log(`%c[Aura Interceptor] ✓✓✓ PII WORK ORDER DETAILS CAPTURED ${frameInfo} ✓✓✓`, 'color: white; background: orange; font-weight: bold; padding: 5px;');
      console.log('%c[Aura Interceptor] URL:', 'color: orange;', url);
      console.log('%c[Aura Interceptor] Method:', 'color: orange;', method);
      console.log('%c[Aura Interceptor] Body length:', 'color: orange;', body.length);
      console.log(`%c[Aura Interceptor] Frame: ${frameInfo}`, 'color: orange; font-weight: bold;');

      // Create request object with name "PII Details"
      const request = {
        name: 'PII Details',
        url: url,
        method: method || "POST",
        body: body,
        referer: location.href,
        userAgent: navigator.userAgent,
        acceptLanguage: navigator.languages?.join(",") || navigator.language || "",
        timestamp: Date.now()
      };

      // Keep only this PII Details in temporary list
      const headerRequest = capturedRequests.find(req => req.name === 'HEADER');
      const workOrdersRequest = capturedRequests.find(req => req.name === 'Work Orders List');

      capturedRequests = [headerRequest, workOrdersRequest, request].filter(Boolean);

      // Send to content script via custom event
      try {
        window.dispatchEvent(new CustomEvent('aura-interceptor-request', {
          detail: {
            request: request,
            replaceAll: false
          }
        }));
        console.log('%c[Aura Interceptor] ✓ PII Details sent to content script (keeping only most recent)', 'color: orange; font-weight: bold;');
      } catch (err) {
        console.error('%c[Aura Interceptor] Error sending event:', 'color: red;', err);
      }

      // Generate and display cURL in console
      generateAndLogCurl(url, method, body, origin);
      return;
    }

    // ============================================================
    // CHECK 2: Work Orders List (RecordGvp.getRecord in URL)
    // ============================================================
    if (url.includes("ui-force-components-controllers-recordGlobalValueProvider.RecordGvp.getRecord=1")) {
      console.log(`%c[Aura Interceptor] ✓✓✓ WORK ORDERS LIST REQUEST CAPTURED ${frameInfo} ✓✓✓`, 'color: white; background: blue; font-weight: bold; padding: 5px;');
      console.log('%c[Aura Interceptor] URL:', 'color: blue;', url);
      console.log('%c[Aura Interceptor] Method:', 'color: blue;', method);
      console.log('%c[Aura Interceptor] Body length:', 'color: blue;', body.length);
      console.log(`%c[Aura Interceptor] Frame: ${frameInfo}`, 'color: blue; font-weight: bold;');

      // Create request object with name "Work Orders List"
      const request = {
        name: 'Work Orders List',
        url: url,
        method: method || "POST",
        body: body,
        referer: location.href,
        userAgent: navigator.userAgent,
        acceptLanguage: navigator.languages?.join(",") || navigator.language || "",
        timestamp: Date.now()
      };

      // Keep only this Work Orders List in temporary list
      const headerRequest = capturedRequests.find(req => req.name === 'HEADER');
      if (headerRequest) {
        capturedRequests = [headerRequest, request];
      } else {
        capturedRequests = [request];
      }

      // Send to content script via custom event (normal mode - content.js will handle filtering)
      try {
        window.dispatchEvent(new CustomEvent('aura-interceptor-request', {
          detail: {
            request: request,
            replaceAll: false // Content script will handle keeping only 1
          }
        }));
        console.log('%c[Aura Interceptor] ✓ Work Orders List sent to content script (keeping only most recent)', 'color: blue; font-weight: bold;');
      } catch (err) {
        console.error('%c[Aura Interceptor] Error sending event:', 'color: red;', err);
      }

      // Generate and display cURL in console
      generateAndLogCurl(url, method, body, origin);
      return;
    }

    // ============================================================
    // CHECK 2: HEADER (Technician_Work_Order_List_View)
    // ============================================================
    const raw_message = getRawPair("message", body);

    if (!raw_message) {
      console.log('%c[Aura Interceptor] ❌ No "message" parameter, ignoring', 'color: orange;');
      return;
    }

    const listView = extractListViewFromMessage(raw_message);
    console.log('%c[Aura Interceptor] ListView detected:', 'color: blue;', listView);

    if (listView !== "Technician_Work_Order_List_View") {
      console.log('%c[Aura Interceptor] ❌ ListView does not match:', 'color: orange;', listView, '!== "Technician_Work_Order_List_View"');
      console.log('%c[Aura Interceptor] Request ignored', 'color: orange;');
      return;
    }

    console.log(`%c[Aura Interceptor] ✓✓✓ HEADER REQUEST CAPTURED ${frameInfo} ✓✓✓`, 'color: white; background: green; font-weight: bold; padding: 5px;');
    console.log('%c[Aura Interceptor] ListView:', 'color: green;', listView);
    console.log('%c[Aura Interceptor] URL:', 'color: green;', url);
    console.log('%c[Aura Interceptor] Method:', 'color: green;', method);
    console.log('%c[Aura Interceptor] Body length:', 'color: green;', body.length);
    console.log(`%c[Aura Interceptor] Frame: ${frameInfo}`, 'color: green; font-weight: bold;');

    // Create request object with special name "HEADER"
    const request = {
      name: 'HEADER',
      url: url,
      method: method || "POST",
      body: body,
      referer: location.href,
      userAgent: navigator.userAgent,
      acceptLanguage: navigator.languages?.join(",") || navigator.language || "",
      timestamp: Date.now(),
      listView: listView
    };

    // Clear temporary list and keep only this one (HEADER)
    capturedRequests = [request];

    // Send to content script via custom event with replace instruction
    try {
      window.dispatchEvent(new CustomEvent('aura-interceptor-request', {
        detail: {
          request: request,
          replaceAll: true // Indicate that all should be replaced
        }
      }));
      console.log('%c[Aura Interceptor] ✓ HEADER sent to content script (replacing previous records)', 'color: green; font-weight: bold;');
    } catch (err) {
      console.error('%c[Aura Interceptor] Error sending event:', 'color: red;', err);
    }

    // Generate and display cURL in console
    generateAndLogCurl(url, method, body, origin);
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

  function generateAndLogCurl(url, method, body, origin) {
    const referer = location.href;
    const ua = navigator.userAgent;
    const acceptLang = navigator.languages?.join(",") || navigator.language || "";

    // Get saved cookie WITHOUT decoding (raw)
    const cookieHeader = localStorage.getItem('aura_interceptor_cookie') || '<COOKIE_HERE>';

    let L = [];
    L.push("\n✅ cURL DECODED (human-readable JSON):\n");
    L.push(`curl '${url}' \\`);
    L.push(`  -X ${method || "POST"} \\`);
    L.push(`  -H 'Accept: application/json' \\`);
    L.push(`  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \\`);
    L.push(`  -H 'Origin: ${origin}' \\`);
    L.push(`  -H 'Referer: ${referer}' \\`);
    L.push(`  -H 'User-Agent: ${ua}' \\`);
    L.push(`  -H 'Accept-Language: ${acceptLang}' \\`);
    L.push(`  -H 'Cache-Control: no-cache' \\`);
    L.push(`  -H 'Pragma: no-cache' \\`);
    L.push(`  -H 'Cookie: ${cookieHeader}' \\`);

    // Extract raw parameters and DECODE them
    const raw_message = getRawPair("message", body);
    const raw_context = getRawPair("aura.context", body);
    const raw_page = getRawPair("aura.pageURI", body);
    const raw_token = getRawPair("aura.token", body);

    // Debug: Log token extraction
    if (raw_token) {
      const decoded_token_debug = decodeParameter(raw_token);
      console.log('%c[Aura Interceptor] 🔑 TOKEN EXTRACTED:', 'color: magenta; font-weight: bold;');
      console.log('%c[Aura Interceptor] Raw token (first 100 chars):', 'color: magenta;', raw_token.substring(0, 100));
      console.log('%c[Aura Interceptor] Decoded token (first 100 chars):', 'color: magenta;', decoded_token_debug ? decoded_token_debug.substring(0, 100) : 'null');
    } else {
      console.log('%c[Aura Interceptor] ❌ NO TOKEN FOUND in body', 'color: red; font-weight: bold;');
    }

    if (raw_message) {
      // DECODE all parameters for human-readable output
      const decoded_message = decodeParameter(raw_message);
      const decoded_context = decodeParameter(raw_context);
      const decoded_page = decodeParameter(raw_page);
      const decoded_token = decodeParameter(raw_token);

      // message uses --data-raw (decoded, human-readable)
      L.push(`  --data-raw '${decoded_message}' \\`);

      // aura.context, aura.pageURI, aura.token use --data-urlencode (curl will encode them)
      if (decoded_context) L.push(`  --data-urlencode '${decoded_context}' \\`);
      if (decoded_page) L.push(`  --data-urlencode '${decoded_page}' \\`);
      if (decoded_token) L.push(`  --data-urlencode '${decoded_token}'`);
    } else {
      // For requests without standard parameters, use entire body as-is
      L.push(`  --data-raw '${body}'`);
    }

    console.log(L.join("\n"));
    console.log("\n📌 cURL ready to copy (decoded, human-readable)\n");
  }

  // Intercept fetch
  console.log('%c[Aura Interceptor] Intercepting window.fetch...', 'color: blue;');
  const origFetch = window.fetch;
  window.fetch = function (input, init = {}) {
    try {
      const rawUrl = typeof input === "string" ? input : input.url;
      const method = init?.method || "GET";
      const body = init?.body;

      console.log('%c[Aura Interceptor] [FETCH] Detected:', 'color: purple;', rawUrl);

      // Accept both /s/sfsites/aura AND /aura (for iframe requests)
      if (
        (rawUrl.includes("/s/sfsites/aura") || rawUrl.includes("/aura?")) &&
        method.toUpperCase() === "POST" &&
        typeof body === "string"
      ) {
        buildCurlAndStore(rawUrl, method, body);
      }
    } catch (err) {
      console.error('%c[Aura Interceptor] [FETCH] Error:', 'color: red;', err);
    }
    return origFetch.apply(this, arguments);
  };
  console.log('%c[Aura Interceptor] ✓ fetch intercepted', 'color: green;');

  // Intercept XMLHttpRequest
  console.log('%c[Aura Interceptor] Intercepting XMLHttpRequest...', 'color: blue;');
  const origOpen = XMLHttpRequest.prototype.open;
  const origSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url) {
    this._url = url;
    this._method = method;
    console.log('%c[Aura Interceptor] [XHR] open:', 'color: purple;', method, url);
    return origOpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function (body) {
    try {
      console.log('%c[Aura Interceptor] [XHR] send:', 'color: purple;', this._url);

      // Accept both /s/sfsites/aura AND /aura (for iframe requests)
      if (
        this._url && (this._url.includes("/s/sfsites/aura") || this._url.includes("/aura?")) &&
        this._method && this._method.toUpperCase() === "POST" &&
        typeof body === "string"
      ) {
        buildCurlAndStore(this._url, this._method, body);
      }
    } catch (err) {
      console.error('%c[Aura Interceptor] [XHR] Error:', 'color: red;', err);
    }
    return origSend.apply(this, arguments);
  };
  console.log('%c[Aura Interceptor] ✓ XMLHttpRequest intercepted', 'color: green;');

  console.log('%c[Aura Interceptor] ========== READY ========== ', 'color: white; background: green; font-weight: bold; padding: 5px 10px;');
  console.log('%c[Aura Interceptor] Interceptor active. Make requests to see them captured.', 'color: green; font-weight: bold;');

  // Expose global function for debugging
  window.__auraInterceptor = {
    getRequests: () => capturedRequests,
    clearRequests: () => { capturedRequests = []; },
    version: '2.0.0'
  };
})();
