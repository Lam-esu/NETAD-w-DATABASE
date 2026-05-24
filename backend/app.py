from datetime import datetime, timedelta
import csv
import io
import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, jsonify, session, Response, send_from_directory
from flask_cors import CORS
from werkzeug.utils import safe_join

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

app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path=""
)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1
)

app.config.from_object(Config)

# SESSION SECURITY
app.config["SESSION_COOKIE_HTTPONLY"] = True

# Railway HTTPS fix
app.config["SESSION_COOKIE_SAMESITE"] = "None"

# MUST be True for Railway HTTPS
app.config["SESSION_COOKIE_SECURE"] = True

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

CORS(
    app,
    supports_credentials=True,
    origins=[
        "https://web-production-e808b.up.railway.app"
    ]
)

db.init_app(app)
bcrypt.init_app(app)
limiter.init_app(app)

camera_service = CameraService(app.config["CAMERA_SOURCE"])

app.after_request(add_security_headers)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "Correct app.py is running"
    })


# =====================================================
# FRONTEND ROUTES
# =====================================================

@app.route("/")
def serve_login():
    return send_from_directory("frontend", "index.html")


@app.route("/<path:filename>")
def serve_frontend(filename):
    safe_path = safe_join("frontend", filename)

    if safe_path is None:
        return jsonify({"error": "Invalid file path"}), 400

    return send_from_directory("frontend", filename)

# =====================================================
# SETUP DEFAULT ADMIN
# =====================================================

@app.route("/api/setup", methods=["POST"])
def setup_admin():
    existing_admin = User.query.filter_by(username="admin").first()

    if existing_admin:
        return jsonify({"message": "Admin already exists"}), 200

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
# AUTH ROUTES
# =====================================================

@app.route("/api/auth/register", methods=["POST"])
@admin_required
def register():

    data = request.get_json() or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "user")

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

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({
            "error": "Username already exists"
        }), 409

    user = User(
        username=username,
        email=email,
        role=role
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


@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():

    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()

    if not user:
        write_audit_log(username, "Failed login: user not found")

        return jsonify({
            "error": "Invalid username or password"
        }), 401

    if user.locked_until and datetime.utcnow() < user.locked_until:
        write_audit_log(username, "Blocked login: account locked")

        return jsonify({
            "error": "Account temporarily locked"
        }), 423

    if not user.is_active:
        write_audit_log(username, "Blocked login: inactive account")

        return jsonify({
            "error": "Account disabled"
        }), 403

    if not user.check_password(password):

        user.failed_attempts += 1

        if user.failed_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)

            write_audit_log(
                username,
                "Account locked after failed attempts"
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

    user.failed_attempts = 0
    user.locked_until = None

    db.session.commit()

    session.permanent = True
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    write_audit_log(user.username, "Logged in")

    return jsonify({
        "message": "Login successful",
        "user": {
            "username": user.username,
            "role": user.role
        }
    })


@app.route("/api/auth/me", methods=["GET"])
@login_required
def current_user():
    return jsonify({
        "username": session.get("username"),
        "role": session.get("role")
    })


@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():

    username = session.get("username")

    write_audit_log(username, "Logged out")

    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    })

# DASHBOARD


@app.route("/api/dashboard/stats", methods=["GET"])
@login_required
def dashboard_stats():

    total_users = User.query.count()
    total_logs = AuditLog.query.count()

    write_audit_log(
        session.get("username"),
        "Viewed dashboard"
    )

    return jsonify({
        "camera_status": "ONLINE",
        "online_cameras": 1,
        "active_users": total_users,
        "total_logs": total_logs,
        "devices": total_users
    })


# CAMERA


@app.route("/api/camera/stream")
@login_required
def camera_stream():

    write_audit_log(
        session.get("username"),
        "Accessed CCTV stream"
    )

    return Response(
        camera_service.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/camera/status", methods=["GET"])
@login_required
def camera_status():

    is_online = camera_service.connect()

    return jsonify({
        "camera": "Main CCTV Camera",
        "status": "ONLINE" if is_online else "OFFLINE"
    })


# LOGS


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

    write_audit_log(
        session.get("username"),
        "Viewed audit logs"
    )

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
    ])


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
        "Exported audit logs"
    )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=audit_logs.csv"
        }
    )


# USERS


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
    ])


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
    })


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
        "message": "User deleted successfully"
    })


@app.route("/api/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def reset_user_password(user_id):

    data = request.get_json() or {}

    new_password = data.get("password", "")

    if len(new_password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    user = User.query.get_or_404(user_id)

    user.set_password(new_password)

    user.failed_attempts = 0
    user.locked_until = None

    db.session.commit()

    write_audit_log(
        session.get("username"),
        f"Reset password for user: {user.username}"
    )

    return jsonify({
        "message": "Password reset successfully"
    })


# SETTINGS


@app.route("/api/settings/save", methods=["POST"])
@admin_required
def save_settings():
    
    data = request.get_json() or {}

    auto_logout = data.get("auto_logout", "30")

    write_audit_log(
        session.get("username"),
        f"Changed auto logout to {auto_logout} minutes"
    )

    return jsonify({
        "message": "Settings saved"
    })
# INIT DATABASE ON STARTUP
with app.app_context():
    db.create_all()

# INIT DB

    
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized successfully.")

# RUN APP

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=False
)