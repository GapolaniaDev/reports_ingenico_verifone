# Quick Start Guide - Verifone Invoice Web App

## 🚀 Start in 3 Steps

### Step 1: Install Dependencies

```bash
./start_server.sh
```

Or manually:

```bash
pip3 install -r requirements.txt
python3 app.py
```

### Step 2: Access the Web Interface

Open your browser and go to:
```
http://localhost:8080
```

### Step 3: Update Credentials

1. Click on "Credentials" in the navigation
2. Open Verifone in another browser tab
3. Open DevTools (Press F12)
4. Go to Network tab
5. Navigate to the Work Orders page
6. Find the request to `aura`
7. **Copy ALL the request information** (see example below)
8. Paste it in the "Request Text" box
9. Select "HEADER" as credential type
10. Click "Parse & Update Credentials"

---

## 📋 What to Copy from Browser

When you're in the Network tab and have selected the `aura` request, you need to copy information like this:

### From the "Headers" tab, copy:

```
Request URL
https://verifone123.my.site.com/verifonefs/s/sfsites/aura?r=22&...
Request Method
POST
cookie
renderCtx=%7B%22pageId%22%3A%22...%22%7D; CookieConsentPolicy=0:1; BrowserId=...; sid=...
```

### From the "Payload" or "Request" tab, copy:

```
message
{"actions":[...]}
aura.context
{"mode":"PROD",...}
aura.token
eyJub25jZSI6Ijd5...
```

**Just select all the text** and paste it into the web form. The app will parse it automatically!

---

## 🎯 How to Use

### Generate Invoice

1. Make sure credentials are updated (see Step 3 above)
2. Go to Dashboard
3. Click "Generate Invoice"
4. Wait for progress to complete
5. Click "View Latest Invoice"

### Update Different Credential Types

The app needs 3 types of credentials:

| Type | When to Update | What Request to Copy |
|------|---------------|---------------------|
| **HEADER** | First time or when list doesn't load | Request when loading Work Orders list |
| **FIRST** | When work order details fail | Request when clicking on a specific Work Order |
| **PII** | When terminal/address info is missing | Request when viewing Work Order PII details |

**Pro Tip**: Update all 3 at once by:
1. Load Work Orders list → Copy request → Update HEADER
2. Click on one Work Order → Copy request → Update FIRST
3. Wait for PII section to load → Copy request → Update PII

---

## 🔍 Understanding the Request Format

The app accepts TWO formats:

### Format 1: Plain Text (Easiest!)

Just copy-paste all the text you see in DevTools:

```
Request URL
https://...
Request Method
POST
cookie
sid=...
aura.token
eyJ...
```

### Format 2: cURL Command

Right-click on request → Copy → Copy as cURL:

```
curl 'https://...' \
  -H 'Cookie: sid=...' \
  --data 'aura.token=...'
```

Both formats work! Use whichever is easier for you.

---

## ⚡ Quick Commands

```bash
# Start server
./start_server.sh

# Or manually
python3 app.py

# Install/Update dependencies
pip3 install -r requirements.txt

# Check if server is running
curl http://localhost:5000/api/generation-status
```

---

## 🐛 Troubleshooting

### "No cookies found"
- Make sure you copied the **entire** request including headers
- Look for a line that starts with `cookie` or `Cookie:`

### "Invoice generation fails"
1. Update HEADER credentials first
2. Generate invoice
3. If it fails, check which step failed and update that credential type

### "Port 8080 already in use"
```bash
# Kill the process using port 8080
lsof -ti:8080 | xargs kill -9

# Then restart
python3 app.py
```

###  "Module not found"
```bash
# Reinstall dependencies
pip3 install --upgrade -r requirements.txt
```

---

## 📱 Browser Compatibility

Works best with:
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge

---

## 🎉 You're Ready!

Once you see this in your terminal:

```
* Running on http://0.0.0.0:8080
* Running on http://127.0.0.1:8080
```

Open http://localhost:8080 in your browser and start managing invoices!

---

## 📚 Need More Help?

Read the full documentation in `README_WEB_APP.md`
