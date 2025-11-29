# Verifone Invoice Management - Web Application

## Overview

This is a Flask-based web application that provides a powerful interface to manage Verifone invoices, credentials, and automate invoice generation.

## Features

1. **Credentials Management**: Update and manage API credentials directly from the browser
2. **Request Parser**: Paste browser requests (from DevTools) and automatically convert them to proper credentials
3. **Automated Invoice Generation**: Generate invoices with a single click
4. **Invoice Viewer**: View and export generated invoices directly in the browser

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Install required dependencies:

```bash
pip install flask python-dotenv requests
```

2. Make sure you have a `.env` file with your credentials (see `.env.example`)

3. Run the application:

```bash
python app.py
```

4. Open your browser and navigate to:

```
http://localhost:5000
```

## Usage

### 1. Dashboard

The main dashboard provides quick access to all features:
- Generate new invoices
- Manage credentials
- View latest invoices

### 2. Updating Credentials

There are two ways to update credentials:

#### Option A: Paste Browser Request (Recommended)

1. Go to `/credentials` page
2. Open Verifone site in browser
3. Open DevTools (F12) → Network tab
4. Perform the action you want to capture (e.g., load Work Orders list)
5. Find the request to `aura`
6. **Copy the request details** by selecting all text in the Headers/Payload tabs
7. Paste into the "Request Text" box
8. Select the credential type (HEADER, FIRST, or PII)
9. Click "Parse & Update"

#### Option B: Use CURL Command

1. In DevTools, right-click on the request
2. Select "Copy → Copy as cURL"
3. Paste the CURL command in the text box
4. Select the credential type
5. Click "Parse & Update"

### 3. Generating Invoices

1. From the Dashboard, click "Generate Invoice"
2. The system will:
   - Fetch all Work Orders
   - Make parallel requests to get details
   - Calculate charges automatically
   - Generate HTML invoice
3. Monitor progress in real-time
4. When complete, view/download the invoice

### 4. Viewing Invoices

1. Go to `/viewer` page
2. The latest invoice will load automatically
3. Use the filters to search and sort
4. Export to Excel with properly formatted sheets

## API Endpoints

### POST `/api/parse-request`

Parse a browser request and extract credentials.

**Request:**
```json
{
  "request_text": "curl 'https://...' or plain text from browser",
  "credential_type": "HEADER"
}
```

**Response:**
```json
{
  "success": true,
  "credentials": {...},
  "message": "Extracted 15 credentials successfully"
}
```

### POST `/api/update-credentials`

Update credentials in `.env` file.

**Request:**
```json
{
  "credentials": {
    "COOKIE_SID": "...",
    "AURA_TOKEN_HEADER": "..."
  }
}
```

### POST `/api/generate-invoice`

Start invoice generation process.

**Response:**
```json
{
  "success": true,
  "message": "Invoice generation started"
}
```

### GET `/api/generation-status`

Get current status of invoice generation.

**Response:**
```json
{
  "running": true,
  "progress": 45,
  "total": 100,
  "message": "Processing work order 45/100...",
  "result_file": null
}
```

## How the Browser Request Parser Works

The parser can handle two formats:

### Format 1: Plain Text from Browser DevTools

Copy all this text from the request in DevTools:

```
Request URL
https://verifone123.my.site.com/verifonefs/s/sfsites/aura?r=22&...
Request Method
POST
cookie
renderCtx=%7B%22pageId%22...; CookieConsentPolicy=0:1; ...
content-type
application/x-www-form-urlencoded; charset=UTF-8
form data
message
{"actions":[...]}
aura.context
{"mode":"PROD",...}
aura.token
eyJub25jZSI...
```

The parser will:
1. Extract the URL
2. Parse all headers
3. Extract form data
4. Convert to a proper CURL command
5. Extract credentials

### Format 2: CURL Command

Just paste the complete CURL command copied from DevTools.

## File Structure

```
Invoice OCT 2025/
├── app.py                    # Main Flask application
├── generate_invoice.py       # Invoice generation logic
├── update_credentials.py     # Credential update logic
├── debug_curl.py            # CURL debugging tool
├── .env                     # Environment variables (credentials)
├── templates/               # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Dashboard
│   ├── credentials.html    # Credentials management
│   └── viewer.html         # Invoice viewer
├── static/                 # Static files (CSS, JS)
├── VerifoneWorkOrders/     # Generated invoices
└── index.html              # Standalone invoice viewer
```

## Troubleshooting

### Issue: "No cookies found in CURL command"

**Solution**: Make sure you're copying the complete request with headers, especially the `Cookie:` header.

### Issue: "Invoice generation fails"

**Solution**:
1. Check that credentials are up to date
2. Try updating each credential type (HEADER, FIRST, PII) separately
3. Check the console for specific error messages

### Issue: "Can't connect to server"

**Solution**:
1. Make sure Flask is running (`python app.py`)
2. Check that port 5000 is not in use
3. Try accessing `http://127.0.0.1:5000` instead of `localhost`

## Security Notes

- Never commit your `.env` file to Git
- Keep your credentials private
- The web application should only run locally (not exposed to internet)
- Consider adding authentication if deploying to a server

## Development

To add new features:

1. Add routes in `app.py`
2. Create templates in `templates/`
3. Add static files (CSS/JS) in `static/`
4. Update this README

## Credits

Created for automated Verifone invoice management.
