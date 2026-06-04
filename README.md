# NETAD Secure CCTV Monitoring System

A secure Flask-based CCTV monitoring website with login/logout, role-based access control, audit logs, user management, account lockout, two-factor authentication, and a CCTV stream relay for cloud deployment.

## Features

- Secure login and logout with Flask sessions
- Admin and user roles
- Admin-only Logs and Users pages
- Audit logging for user activity
- Account lockout after 3 failed login attempts
- Two-factor authentication using authenticator apps
- Dashboard camera status and live camera feed
- Tapo C200 RTSP support through OpenCV
- Railway PostgreSQL database support
- CCTV cloud access through a local relay and tunnel such as Tailscale Funnel or ngrok static domain

## Project Structure

```text
NETAD-w-DATABASE/
├── backend/
│   ├── app.py
│   ├── camera.py
│   ├── camera_relay.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── requirements.txt
│   ├── security.py
│   └── frontend/
│       ├── index.html
│       ├── dashboard.html
│       ├── cameras.html
│       ├── logs.html
│       ├── admin.html
│       ├── settings.html
│       ├── setup-2fa.html
│       ├── verify-2fa.html
│       ├── style.css
│       └── js/
│           ├── auth.js
│           ├── login.js
│           ├── dashboard.js
│           ├── admin.js
│           ├── logs.js
│           ├── settings.js
│           ├── setup-2fa.js
│           └── verify-2fa.js
├── requirements.txt
├── Procfile
├── .gitignore
└── README.md
```

## Network Diagram

```mermaid
flowchart LR
    A[Tapo C200 CCTV] -->|RTSP stream| B[Mac / Local Relay]
    B -->|camera_relay.py on port 5050| C[Tailscale Funnel or ngrok]
    C -->|HTTPS public URL| D[Railway Flask Web App]
    D -->|/api/camera/status and /api/camera/stream| E[Browser Dashboard]
    D -->|DATABASE_URL| F[Railway PostgreSQL]
```

### Plain Network Diagram

```text
Tapo C200 CCTV
    ↓ RTSP
Mac / Local camera_relay.py
    ↓ HTTPS tunnel
Tailscale Funnel or ngrok static domain
    ↓ CAMERA_SOURCE / CAMERA_STATUS_URL
Railway Flask App
    ↓
Dashboard / Cameras page
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Lam-esu/NETAD-w-DATABASE.git
cd NETAD-w-DATABASE
```

### 2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `backend/.env`

Do not commit this file.

```env
SECRET_KEY=
DATABASE_URL=
CAMERA_SOURCE=
RELAY_TOKEN=
```

Generate a secure relay token:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 5. Run locally

```bash
cd backend
python3 app.py
```

Open:

```text
http://127.0.0.1:8000
```

### 6. Create default admin

In another terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/setup
```

Default login:

```text
Username: admin
Password: admin123
```

Change this password before production use.

## Tapo C200 RTSP Setup

In the Tapo app:

```text
Camera → Settings → Advanced Settings → Camera Account
```

Create a camera account. Use that account for RTSP, not your Tapo app login.

RTSP examples:

```text
High quality: rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream1
Lower quality: rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream2
```

Test first in VLC:

```text
VLC → File → Open Network → paste RTSP URL
```

## Railway Deployment

### Required Railway variables

Set these in Railway → web service → Variables:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=your-long-random-secret
CAMERA_SOURCE=https://your-funnel-url/camera-stream?token=YOUR_RELAY_TOKEN
CAMERA_STATUS_URL=https://your-funnel-url/camera-status?token=YOUR_RELAY_TOKEN
```

If you are not using a tunnel yet, leave camera variables blank:

```env
CAMERA_SOURCE=
CAMERA_STATUS_URL=
```

### Start command

If Railway root is the repository root:

```bash
gunicorn backend.app:app --bind 0.0.0.0:$PORT
```

If Railway root is `backend`, use:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

## CCTV Cloud Setup with Tailscale Funnel

Your ISP uses CGNAT if your router WAN IP is private such as `10.x.x.x`, so normal port forwarding will not work. Use Tailscale Funnel or another tunnel.

### 1. Run local camera relay

```bash
cd "/Users/lamuelalojado/Documents/NETAD 2FA BACKUP w: SECURITY/backend"
source "../.venv/bin/activate"
python3 camera_relay.py
```

### 2. Start Tailscale Funnel

```bash
sudo tailscale funnel --https=8443 http://127.0.0.1:5050
```

### 3. Check status

```bash
tailscale funnel status
```

Example public URL:

```text
https://esus-macbook.tail4f04e7.ts.net:8443/
```

Railway variables should be:

```env
CAMERA_SOURCE=https://esus-macbook.tail4f04e7.ts.net:8443/camera-stream?token=YOUR_RELAY_TOKEN
CAMERA_STATUS_URL=https://esus-macbook.tail4f04e7.ts.net:8443/camera-status?token=YOUR_RELAY_TOKEN
```

## CCTV Cloud Setup with ngrok Static Domain

Start relay:

```bash
cd backend
python3 camera_relay.py
```

Start ngrok with your static domain:

```bash
ngrok http --url=YOUR_STATIC_DOMAIN.ngrok-free.dev 5050
```

Railway variables:

```env
CAMERA_SOURCE=https://YOUR_STATIC_DOMAIN.ngrok-free.dev/camera-stream?token=YOUR_RELAY_TOKEN
CAMERA_STATUS_URL=https://YOUR_STATIC_DOMAIN.ngrok-free.dev/camera-status?token=YOUR_RELAY_TOKEN
```

## Two-Factor Authentication Flow

1. Admin creates a user.
2. New user logs in with username/password.
3. If the user has no 2FA secret, they are redirected to `setup-2fa.html`.
4. User adds the setup key to Google Authenticator or Microsoft Authenticator.
5. User enters the generated 6-digit code.
6. Future logins require `verify-2fa.html`.

## Screenshots

Screenshots are included in the `screenshots/` folder:

- `login_page.png`
- `dashboard_camera_status.png`
- `railway_http_logs.png`
- `cgnat_wan_ip.png`
- `ngrok_static_domain.png`
- `vlc_open_network.png`

## Security Notes

- Do not commit `.env` files.
- Do not commit SQLite `.db` files.
- Change the default admin password.
- Change any camera password or relay token that was shared publicly.
- Use strong passwords for Tapo Camera Account and web users.
- Keep `SECRET_KEY` stable on Railway. Changing it invalidates sessions.
- Do not expose raw RTSP credentials directly to frontend HTML.
- Prefer tunnel relay over direct camera port forwarding.

## Common Issues

### Railway says camera unavailable

Check:

```text
camera_relay.py is running
Tailscale Funnel/ngrok is running
CAMERA_SOURCE is correct
CAMERA_STATUS_URL is correct
Railway was redeployed after variables changed
```

### Camera works on Cameras page but not Dashboard

Make sure `dashboard.html` uses the correct image variable, for example:

```javascript
const cameraPageFeed = document.getElementById("cameraPageFeed");

cameraPageFeed.style.display = "block";
startCameraStream(cameraPageFeed);
```

### Login goes back to login page

Check session settings:

```python
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = IS_PRODUCTION
```

Also verify `/api/auth/me` returns the logged-in user.

## GitHub Push

```bash
git add .
git commit -m "Update documentation and deployment setup"
git pull --rebase origin main
git push origin main
```
