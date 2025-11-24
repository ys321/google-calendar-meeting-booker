# Vaidrix Google Calendar Meeting Booking Chatbot (Flask + LangChain + Gemini)

This is a small reference project that shows how to build a **meeting booking chatbot**
with:

- Flask (backend API)
- LangChain
- Gemini (via `langchain-google-genai`)
- Google Calendar (OAuth, single shared calendar with Google Meet integration)
- Embeddable JS widget for your website (e.g. `https://vaidrix.com/site`)

---

## 1. Setup

### 1.1. Python environment

```bash
python -m venv env
source env/bin/activate   # Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 1.2. Gemini API key

Set this environment variable:

```bash
export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
```

On Windows PowerShell:

```powershell
$env:GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
```

### 1.3. Google OAuth Setup (for Calendar + Meet)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Calendar API** for your project
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
5. Choose **Web application** as the application type
6. Add authorized redirect URI: `http://localhost:5000/auth/google/callback` (for local development)
7. Copy the **Client ID** and **Client Secret**

Set the following environment variables:

```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5000/auth/google/callback"
```

On Windows PowerShell:

```powershell
$env:GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET="your-client-secret"
$env:GOOGLE_REDIRECT_URI="http://localhost:5000/auth/google/callback"
```

### 1.4. Google Calendar Configuration

If you want to use a specific calendar:

```bash
export GOOGLE_CALENDAR_ID="your-calendar-id@group.calendar.google.com"
```

Set your default timezone:

```bash
export DEFAULT_TIMEZONE="Asia/Kolkata"
```

**Note:** On first run, visit `http://localhost:5000/auth/google` to authorize the application. The OAuth token will be saved to `credentials/token.json` automatically.

---

## 2. Run locally

```bash
flask --app app run --debug
```

Open in your browser:

- http://localhost:5000/

**First-time setup:** Before using the chatbot, you need to authorize Google Calendar access:
1. Visit `http://localhost:5000/auth/google` in your browser
2. Sign in with your Google account
3. Grant permissions for Calendar access
4. You'll be redirected back to the chat page

You'll see a small chat UI where you can test the bot, for example:

> "Book a 30 minute call tomorrow at 4pm. My email is john@company.com"

The bot will automatically create Google Meet links for all meetings and send email invitations to attendees.

---

## 3. Deploy & embed on `https://vaidrix.com/site`

### 3.1. Host the Flask app

You can host this app on:

- VPS (Hostinger, etc.) with Gunicorn + Nginx
- Render, Railway, etc.

Expose:

- `POST /api/chat`
- `GET /static/widget.js`
- `GET /auth/google` (OAuth authorization)
- `GET /auth/google/callback` (OAuth callback)

Make sure CORS is allowed (already enabled with `flask_cors.CORS`).

**Important:** Update `GOOGLE_REDIRECT_URI` environment variable to match your production domain:
```bash
export GOOGLE_REDIRECT_URI="https://your-deployed-domain.com/auth/google/callback"
```

### 3.2. Use the widget on your site

On your `https://vaidrix.com/site` HTML, add:

```html
<script>
  // Point to your deployed Flask API endpoint:
  window.VAIDRIX_MEETING_BOT_API = "https://your-deployed-domain.com/api/chat";
</script>
<script src="https://your-deployed-domain.com/static/widget.js" async></script>
```

A round **"V"** bubble will show in the bottom-right corner. Clicking it opens
the chat window that talks to your Flask+LangChain+Gemini backend and can book
meetings in your shared Google Calendar (sending email invites to the client).

---

## 4. Environment Variables Summary

**IMPORTANT:** Create a `.env` file in the project root (copy from `.env.example`) and add your credentials. The `.env` file is excluded from git via `.gitignore` for security.

**Required environment variables:**

```bash
# Required - Gemini API Key
GOOGLE_API_KEY=your-gemini-api-key

# Required - Google OAuth Credentials
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
OAUTHLIB_INSECURE_TRANSPORT=1

# Required - Calendar ID
GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
```

**Optional environment variables:**

```bash
# Optional
DEFAULT_TIMEZONE=Asia/Kolkata
FLASK_SECRET_KEY=your-secret-key
GEMINI_MODEL_NAME=gemini-2.5-pro
```

**Setup steps:**
1. Copy `.env.example` to `.env`: `cp .env.example .env` (Linux/Mac) or copy the file manually (Windows)
2. Fill in all required values in `.env`
3. Never commit `.env` to version control (already excluded via `.gitignore`)

## 5. Security Best Practices

**⚠️ CRITICAL: Before pushing to GitHub, ensure:**

1. ✅ All credentials are in `.env` file (never commit `.env`)
2. ✅ `.gitignore` is configured (already set up)
3. ✅ `credentials/token.json` is excluded (contains OAuth tokens)
4. ✅ No hardcoded secrets in code files
5. ✅ `.env.example` is provided as a template (without real values)

**Files automatically excluded from git:**
- `.env` and `.env.*` files
- `credentials/token.json` and all JSON files in credentials/
- `__pycache__/` directories
- Virtual environment (`env/`, `venv/`)

**OAuth Token Storage:**
- OAuth tokens are stored in `credentials/token.json` (auto-generated after first authorization)
- This file is automatically excluded from git
- Tokens auto-refresh when expired
- On first run, visit `/auth/google` to authorize and generate the token file

## 6. Notes

- This is a starting point. For production:
  - Add logging & error tracking
  - Add auth / rate limiting if needed
  - Fine-tune the system prompt in `chatbot.py`
  - Validate and sanitize user input (especially emails)
  - Use environment-specific OAuth redirect URIs
  - Rotate secrets regularly
  - Use a secure secret key for Flask sessions
- You can adapt the styling of `widget.js` and `templates/index.html` to match
  the Vaidrix brand.
