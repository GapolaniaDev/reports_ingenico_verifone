# 🧾 Invoice Management System

**Complete invoice management system for Verifone and Ingenico**

---

## 📋 Table of Contents

1. [Description](#description)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [API Endpoints](#api-endpoints)
8. [Credentials](#credentials)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Description

Flask web system to automate the generation and management of Verifone and Ingenico work order invoices.

### Technologies:
- **Backend:** Flask (Python 3.9+)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **APIs:** Salesforce Aura, Ingenico Portal
- **Extensions:** Chrome Extension (Aura cURL Interceptor)

---

## ⚡ Quick Start

### 1. Requirements
```bash
Python 3.9+
pip
```

### 2. Installation
```bash
# Clone repository
cd "Invoice OCT 2025"

# Install dependencies
pip3 install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run
```bash
# Option A: Automatic script
./scripts/start_server.sh

# Option B: Manual
python3 app/app.py
```

### 4. Access
Open in browser: **http://localhost:8080**

---

## ✨ Features

### 🔐 Verifone
- ✅ Aura API credential management
- ✅ Automatic invoice generation
- ✅ Date range filtering
- ✅ Automatic charge calculation by area/type
- ✅ "On Site" work order detection
- ✅ Excel export

### 📦 Ingenico
- ✅ "Closed Job List" HTML import
- ✅ Closed job search and download
- ✅ Automatic data parsing
- ✅ Area totals calculation

### 🎨 Interface
- ✅ Modern and responsive dashboard
- ✅ Real-time status indicator
- ✅ Modal notification system
- ✅ Interactive table with sorting
- ✅ Excel export
- ✅ Unified Ingenico + Verifone viewer

---

## 📂 Project Structure

```
Invoice OCT 2025/
├── app/                        # Core application
│   ├── app.py                  # Main Flask app
│   ├── generate_invoice.py     # Verifone generation logic
│   └── config.py               # Configurations
│
├── scripts/                    # Auxiliary scripts
│   ├── fetch_ingenico_closed_jobs.py
│   ├── update_credentials.py
│   └── debug_curl.py
│
├── templates/                  # HTML templates (Jinja2)
│   ├── base.html               # Base template
│   ├── credentials.html        # Credential management
│   ├── viewer.html             # Main viewer
│   └── index.html              # Dashboard
│
├── static/                     # Static files
├── aura-curl-interceptor/      # Chrome extension
│
├── tests/                      # Tests and examples
├── data/                       # Generated data
│   ├── VerifoneWorkOrders/
│   └── logs/
│
└── docs/                       # Documentation
```

---

## ⚙️ Configuration

### Environment Variables (.env)

#### Verifone Aura API
```bash
API_URL_HEADER=https://verifone.lightning.force.com/aura
ORIGIN_URL=https://verifone.lightning.force.com
REFERER_HEADER=https://verifone.lightning.force.com/

# Cookies (get from Chrome DevTools)
AURA_COOKIE="sid=...; ..."
```

#### Ingenico API
```bash
INGENICO_BASE_URL=https://portal.ingenico.com.au
INGENICO_USERNAME=your_username
INGENICO_PASSWORD=your_password
```

### How to Get Credentials

#### Verifone (Aura Cookie)
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Navigate in Verifone Portal
4. Copy Request Headers → Cookie
5. Paste in `.env` → `AURA_COOKIE`

**Or use Chrome extension:**
1. Install `aura-curl-interceptor`
2. Open popup
3. Copy cookie automatically

More details: [docs/CREDENTIALS.md](docs/CREDENTIALS.md)

---

## 🚀 Usage

### Generate Verifone Invoice

1. Go to **http://localhost:8080/viewer**
2. Click **"Generate Invoice"**
3. Select date range
4. Configure record limit
5. Generate

The system:
- Fetches work orders from Salesforce Aura API
- Filters by date (inclusive)
- Automatically calculates charges
- Generates HTML with complete table
- Saves in `VerifoneWorkOrders/invoice_YYYYMMDD_HHMMSS/`

### Load Ingenico File

1. Go to **http://localhost:8080/viewer**
2. In "Ingenico - Closed Job List" section
3. Upload HTML file exported from Ingenico
4. View results in unified table

### Export to Excel

1. Load data (Verifone and/or Ingenico)
2. Click **"Export to Excel"**
3. `.xlsx` file downloads with 3 sheets:
   - All Jobs
   - Ingenico
   - Verifone

---

## 🔌 API Endpoints

### `GET /`
Redirect to `/credentials`

### `GET /credentials`
Credential management page

### `GET /viewer`
Main reports viewer

### `POST /api/generate-invoice`
Generates Verifone invoice

**Body:**
```json
{
  "date_from": "2025-11-01",
  "date_to": "2025-11-29",
  "search_string": "",
  "record_limit": 200
}
```

**Response:**
```json
{
  "success": true,
  "message": "Invoice generation started"
}
```

### `GET /api/generation-status`
Gets current generation status

**Response:**
```json
{
  "running": true,
  "progress": 33,
  "total": 201,
  "message": "Processing...",
  "errors": []
}
```

### `POST /api/save-credentials`
Saves Verifone credentials

### `POST /api/test-connection`
Tests connection with Aura API

---

## 🔐 Credentials

### Verifone Credentials Structure

The system requires Salesforce Aura session cookies:

```
sid=...
clientSrc=...
CookieConsentPolicy=...
LSKey-c$CookieConsentPolicy=...
```

### Expiration
Cookies expire after ~2 hours of inactivity. If you get authentication error, update credentials.

### Security
- ❌ **NEVER** commit `.env` to git
- ✅ `.env` is in `.gitignore`
- ✅ Use `.env.example` as template

---

## 🛠️ Troubleshooting

### Error: "Server connection failed"
**Cause:** Flask server is not running
**Solution:** Run `./scripts/start_server.sh`

### Error: "Authentication failed"
**Cause:** Aura cookies expired
**Solution:** Update cookies in `/credentials`

### Error: "Expected table not found"
**Cause:** Incorrect Ingenico HTML file
**Solution:** Export correct file from Ingenico Portal

### "On Site" jobs not appearing
**Cause:** Status field not detected
**Solution:** Verify that Status field = "On Site" in Salesforce

### Incorrect calculations
**Cause:** Area miscalculated or unrecognized job type
**Solution:** Review `calculateCharge()` in `generate_invoice.py`

---

## 📊 Charge Calculation

### Areas (by Postcode)
- **Area 1:** Adelaide metro (default)
- **Area 2:** Specific postcodes (5110, 5116, 5111, etc.)
- **Area 3:** Remote regions

### Base Rates (Area 1)
- Installation/Swap: **$28.00**
- After Hours: **$80.00**
- Weekend: **$40.00**
- After Hours + Weekend: **$90.00**
- Recovery: **$10.00** (fixed)
- De-installation: **$10.00** (fixed)
- Multiple jobs: **$10.00** (second terminal)

**Note:** Areas 2 and 3 have increased rates. See code for details.

---

## 🎨 Notification System

The system includes professional modal notifications:

- ✅ **Success:** Green - Successful operations
- ⚠️ **Warning:** Yellow - Failed validations
- ❌ **Error:** Red - Critical errors
- ℹ️ **Info:** Blue - General information

Auto-close: 5s (success/info), 8s (warning/error)

---

## 🔄 System Status

Indicator in top right corner:

- ✓ **Ready:** System ready (green, soft pulse)
- ⚙️ **Generating:** Processing (orange, spinner)
- ✓ **Completed:** Finished (bright green)
- ⚠️ **Error:** Error (red, clickable for details)

---

## 📦 Dependencies

See `requirements.txt`:
- Flask
- requests
- python-dotenv

---

## 👨‍💻 Development

### Add new endpoint
1. Edit `app/app.py`
2. Add `@app.route('/new-route')`
3. Restart server

### Modify calculations
1. Edit `app/generate_invoice.py`
2. Function `calculateCharge()`
3. Test with example work orders

### Change styles
1. Edit `templates/base.html` (global styles)
2. Or `templates/viewer.html` (specific styles)

---

## 📝 Changelog

See `docs/CHANGELOG.md` file for complete change history.

---

## 📄 License

Private project - All rights reserved

---

## 🆘 Support

For issues or questions:
1. Review [Troubleshooting](#troubleshooting)
2. Review logs in `data/logs/flask_server.log`
3. Contact developer

---

**Last updated:** November 2025
