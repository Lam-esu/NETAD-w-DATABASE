from datetime import datetime, timedelta
import csv
import io
import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify, session, Response, send_from_directory
from flask_cors import CORS
from werkzeug.utils import safe_join
from werkzeug.middleware.proxy_fix import ProxyFix

import pyotp

from config import Config
from extensions import db, bcrypt, limiter
from models import User, AuditLog
from security import (
    login_required,
    admin_required,
    write_audit_log,
    add_security_headers
)
from camera import CameraService


# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================

load_dotenv()


# =====================================================
# PATH CONFIG
# Since you chose Option 2:
# backend/
# ├── app.py
# └── frontend/
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "frontend"))


# =====================================================
# FLASK APP
# =====================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1
)

app.config.from_object(Config)


# =====================================================
# DATABASE CONFIG
# Local = SQLite
# Railway = PostgreSQL
# =====================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///instance/cctv.db"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# =====================================================
# SESSION SECURITY CONFIG
# =====================================================

IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT") is not None

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)


# =====================================================
# EXTENSIONS
# =====================================================

CORS(
    app,
    supports_credentials=True
)

db.init_app(app)
bcrypt.init_app(app)
limiter.init_app(app)


# =====================================================
# CAMERA CONFIG
# Railway cannot use laptop webcam /dev/video0
# Leave CAMERA_SOURCE blank on Railway
# =====================================================

camera_source = os.getenv("CAMERA_SOURCE", "")

camera_service = (
    CameraService(camera_source)
    if camera_source
    else None
)


# =====================================================
# SECURITY HEADERS
# =====================================================

app.after_request(add_security_headers)


# =====================================================
# FRONTEND ROUTES
# =====================================================

@app.route("/")
def serve_login():
    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


@app.route("/<path:filename>")
def serve_frontend(filename):
    safe_path = safe_join(
        FRONTEND_DIR,
        filename
    )

    if safe_path is None:
        return jsonify({
            "error": "Invalid file path"
        }), 400

    return send_from_directory(
        FRONTEND_DIR,
        filename
    )


# =====================================================
# SETUP DEFAULT ADMIN
# =====================================================

@app.route("/api/setup", methods=["POST"])
def setup_admin():
    existing_admin = User.query.filter_by(
        username="admin"
    ).first()

    if existing_admin:
        return jsonify({
            "message": "Admin already exists"
        }), 200

    admin = User(
        username="admin",
        email="admin@example.com",
        role="admin"
    )

    admin.set_password("admin123")

    db.session.add(admin)
    db.session.commit()

    return jsonify({
        "message": "Default admin created",
        "username": "admin",
        "password": "admin123"
    }), 201


# =====================================================
# REGISTER USER
# Admin only
# =====================================================

@app.route("/api/auth/register", methods=["POST"])
@admin_required
def register():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "user").strip().lower()

    if not username or not email or not password:
        return jsonify({
            "error": "Username, email, and password are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    if role not in ["admin", "user"]:
        return jsonify({
            "error": "Invalid role"
        }), 400

    existing_username = User.query.filter_by(
        username=username
    ).first()

    if existing_username:
        return jsonify({
            "error": "Username already exists"
        }), 409

    existing_email = User.query.filter_by(
        email=email
    ).first()

    if existing_email:
        return jsonify({
            "error": "Email already exists"
        }), 409

    user = User(
        username=username,
        email=email,
        role=role,
        is_active=True,
        failed_attempts=0,
        locked_until=None,
        two_factor_enabled=False,
        two_factor_secret=None
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    write_audit_log(
        session.get("username"),
        f"Created user: {username}"
    )

    return jsonify({
        "message": "User created successfully"
    }), 201


# =====================================================
# LOGIN
# Includes:
# - 3 failed attempts lockout
# - first-time 2FA setup enforcement
# - 2FA verification requirement
# =====================================================

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    user = User.query.filter_by(
        username=username
    ).first()

    if not user:
        write_audit_log(
            username,
            "Failed login: user not found"
        )

        return jsonify({
            "error": "Invalid username or password"
        }), 401

    if user.locked_until and datetime.utcnow() < user.locked_until:
        write_audit_log(
            username,
            "Blocked login: account locked"
        )

        return jsonify({
            "error": "Account temporarily locked. Try again later."
        }), 423

    if not user.is_active:
        write_audit_log(
            username,
            "Blocked login: inactive account"
        )

        return jsonify({
            "error": "Account disabled"
        }), 403

    if not user.check_password(password):
        user.failed_attempts += 1

        if user.failed_attempts >= 3:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)

            write_audit_log(
                username,
                "Account locked after 3 failed login attempts"
            )

        else:
            write_audit_log(
                username,
                "Failed login: wrong password"
            )

        db.session.commit()

        return jsonify({
            "error": "Invalid username or password"
        }), 401

    # Successful password check
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()

    # First-time 2FA setup required
    if not user.two_factor_secret:
        session.clear()
        session["pending_2fa_setup_user_id"] = user.id

        return jsonify({
            "message": "2FA setup required",
            "requires_2fa_setup": True
        }), 200

    # Existing 2FA enabled user must verify code
    if user.two_factor_enabled:
        session.clear()
        session["pending_2fa_user_id"] = user.id
        session.modified = True

        return jsonify({
            "message": "2FA required",
            "requires_2fa": True
        }), 200

    # Fallback normal login
    session.permanent = True
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role.strip().lower()
    session.modified = True

    write_audit_log(
        user.username,
        "Logged in"
    )

    return jsonify({
        "message": "Login successful",
        "requires_2fa": False,
        "requires_2fa_setup": False,
        "user": {
            "username": user.username,
            "role": user.role.strip().lower()
        }
    }), 200


# =====================================================
# VERIFY 2FA LOGIN
# =====================================================

@app.route("/api/auth/verify-2fa", methods=["POST"])
def verify_2fa():
    data = request.get_json() or {}

    code = data.get("code", "").strip()
    user_id = session.get("pending_2fa_user_id")

    if not user_id:
        return jsonify({
            "error": "No pending 2FA session"
        }), 400

    user = User.query.get(user_id)

    if not user or not user.two_factor_secret:
        return jsonify({
            "error": "Invalid 2FA session"
        }), 400

    totp = pyotp.TOTP(user.two_factor_secret)

    if not totp.verify(code, valid_window=1):
        write_audit_log(
            user.username,
            "Failed 2FA verification"
        )

        return jsonify({
            "error": "Invalid 2FA code"
        }), 401

    session.pop("pending_2fa_user_id", None)

    session.permanent = True
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role.strip().lower()
    session.modified = True

    write_audit_log(
        user.username,
        "Logged in with 2FA"
    )

    return jsonify({
        "message": "2FA verified",
        "user": {
            "username": user.username,
            "role": user.role.strip().lower()
        }
    }), 200


# =====================================================
# FIRST-TIME 2FA SETUP
# Used when new user logs in for the first time
# =====================================================

@app.route("/api/auth/2fa/first-setup", methods=["POST"])
def first_setup_2fa():
    user_id = session.get("pending_2fa_setup_user_id")

    if not user_id:
        return jsonify({
            "error": "No pending 2FA setup session"
        }), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    if user.two_factor_secret:
        secret = user.two_factor_secret
    else:
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        user.two_factor_enabled = False
        db.session.commit()

    totp_uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="Secure CCTV System"
    )

    return jsonify({
        "secret": secret,
        "otp_uri": totp_uri
    }), 200


@app.route("/api/auth/2fa/first-enable", methods=["POST"])
def first_enable_2fa():
    data = request.get_json() or {}

    code = data.get("code", "").strip()
    user_id = session.get("pending_2fa_setup_user_id")

    if not user_id:
        return jsonify({
            "error": "No pending 2FA setup session"
        }), 400

    user = User.query.get(user_id)

    if not user or not user.two_factor_secret:
        return jsonify({
            "error": "2FA setup not started"
        }), 400

    totp = pyotp.TOTP(user.two_factor_secret)

    if not totp.verify(code, valid_window=1):
        return jsonify({
            "error": "Invalid 2FA code"
        }), 401

    user.two_factor_enabled = True
    db.session.commit()

    session.pop("pending_2fa_setup_user_id", None)

    session.permanent = True
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role.strip().lower()
    session.modified = True

    write_audit_log(
        user.username,
        "Completed first-time 2FA setup"
    )

    return jsonify({
        "message": "2FA setup completed",
        "user": {
            "username": user.username,
            "role": user.role.strip().lower()
        }
    }), 200


# =====================================================
# OPTIONAL 2FA SETUP FOR ALREADY LOGGED IN USERS
# =====================================================

@app.route("/api/auth/2fa/setup", methods=["POST"])
@login_required
def setup_2fa():
    user = User.query.get(
        session.get("user_id")
    )

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    secret = pyotp.random_base32()

    user.two_factor_secret = secret
    user.two_factor_enabled = False

    db.session.commit()

    totp_uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="Secure CCTV System"
    )

    write_audit_log(
        user.username,
        "Started 2FA setup"
    )

    return jsonify({
        "secret": secret,
        "otp_uri": totp_uri
    }), 200


@app.route("/api/auth/2fa/enable", methods=["POST"])
@login_required
def enable_2fa():
    data = request.get_json() or {}

    code = data.get("code", "").strip()

    user = User.query.get(
        session.get("user_id")
    )

    if not user or not user.two_factor_secret:
        return jsonify({
            "error": "2FA setup not started"
        }), 400

    totp = pyotp.TOTP(user.two_factor_secret)

    if not totp.verify(code, valid_window=1):
        return jsonify({
            "error": "Invalid 2FA code"
        }), 401

    user.two_factor_enabled = True

    db.session.commit()

    write_audit_log(
        user.username,
        "Enabled 2FA"
    )

    return jsonify({
        "message": "2FA enabled successfully"
    }), 200


# =====================================================
# LOGOUT AND CURRENT USER
# =====================================================

@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    write_audit_log(
        session.get("username"),
        "Logged out"
    )

    session.clear()

    return jsonify({
        "message": "Logged out"
    }), 200


@app.route("/api/auth/me", methods=["GET"])
@login_required
def current_user():
    return jsonify({
        "username": session.get("username"),
        "role": session.get("role")
    }), 200


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/api/dashboard/stats", methods=["GET"])
@login_required
def dashboard_stats():
    total_users = User.query.count()
    total_logs = AuditLog.query.count()

    camera_status = (
        "UNAVAILABLE"
        if camera_service is None
        else "ONLINE"
    )

    online_cameras = (
        0
        if camera_service is None
        else 1
    )

    return jsonify({
        "camera_status": camera_status,
        "online_cameras": online_cameras,
        "active_users": total_users,
        "total_logs": total_logs,
        "devices": total_users
    }), 200


# =====================================================
# CAMERA ROUTES
# =====================================================

@app.route("/api/camera/stream")
@login_required
def camera_stream():
    write_audit_log(
        session.get("username"),
        "Accessed CCTV stream"
    )

    if camera_service is None:
        return jsonify({
            "error": "Camera unavailable in cloud deployment"
        }), 503

    return Response(
        camera_service.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/camera/status", methods=["GET"])
@login_required
def camera_status():
    if camera_service is None:
        return jsonify({
            "camera": "Main CCTV Camera",
            "status": "UNAVAILABLE"
        }), 200

    is_online = camera_service.connect()

    return jsonify({
        "camera": "Main CCTV Camera",
        "status": "ONLINE" if is_online else "OFFLINE"
    }), 200


# =====================================================
# AUDIT LOGS
# =====================================================

@app.route("/api/logs", methods=["GET"])
@admin_required
def get_logs():
    username = request.args.get("username", "")
    action = request.args.get("action", "")

    query = AuditLog.query

    if username:
        query = query.filter(
            AuditLog.username.contains(username)
        )

    if action:
        query = query.filter(
            AuditLog.action.contains(action)
        )

    logs = query.order_by(
        AuditLog.created_at.desc()
    ).limit(200).all()

    return jsonify([
        {
            "id": log.id,
            "username": log.username,
            "action": log.action,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for log in logs
    ]), 200


@app.route("/api/logs/export", methods=["GET"])
@admin_required
def export_logs():
    logs = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Username",
        "Action",
        "IP Address",
        "User Agent",
        "Timestamp"
    ])

    for log in logs:
        writer.writerow([
            log.id,
            log.username,
            log.action,
            log.ip_address,
            log.user_agent,
            log.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    write_audit_log(
        session.get("username"),
        "Exported audit logs as CSV"
    )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=audit_logs.csv"
        }
    )


# =====================================================
# USER MANAGEMENT
# =====================================================

@app.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for user in users
    ]), 200


@app.route("/api/users/<int:user_id>/disable", methods=["POST"])
@admin_required
def disable_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.username == "admin":
        return jsonify({
            "error": "Default admin cannot be disabled"
        }), 400

    user.is_active = False
    db.session.commit()

    write_audit_log(
        session.get("username"),
        f"Disabled user: {user.username}"
    )

    return jsonify({
        "message": "User disabled"
    }), 200


@app.route("/api/users/<int:user_id>/delete", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.username == "admin":
        return jsonify({
            "error": "Default admin cannot be deleted"
        }), 400

    username = user.username

    db.session.delete(user)
    db.session.commit()

    write_audit_log(
        session.get("username"),
        f"Deleted user: {username}"
    )

    return jsonify({
        "message": "User deleted"
    }), 200


@app.route("/api/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    data = request.get_json() or {}

    new_password = data.get("password", "").strip()

    if len(new_password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    user = User.query.get_or_404(user_id)

    user.set_password(new_password)

    user.failed_attempts = 0
    user.locked_until = None

    # Force user to set up 2FA again after password reset
    user.two_factor_enabled = False
    user.two_factor_secret = None

    db.session.commit()

    write_audit_log(
        session.get("username"),
        f"Reset password for user: {user.username}"
    )

    return jsonify({
        "message": "Password reset successfully"
    }), 200


# =====================================================
# SETTINGS
# =====================================================

@app.route("/api/settings/save", methods=["POST"])
@admin_required
def save_settings():
    data = request.get_json() or {}

    auto_logout = data.get(
        "auto_logout",
        "30"
    )

    write_audit_log(
        session.get("username"),
        f"Changed auto logout setting to {auto_logout} minutes"
    )

    return jsonify({
        "message": "Settings saved"
    }), 200


# =====================================================
# CLI INIT DB
# =====================================================

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized successfully.")


# =====================================================
# CREATE TABLES ON STARTUP
# =====================================================

with app.app_context():
    db.create_all()


# =====================================================
# LOCAL RUN
# =====================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=False
    )