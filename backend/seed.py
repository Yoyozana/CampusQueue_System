"""
Creates all tables (if not already present via schema.sql) and one admin
account. Run locally or via Render's shell, AFTER setting environment
variables / creating your .env file:

    python seed.py

You will be prompted for the admin's name, username, email, and password
so no credentials are ever hardcoded or committed to GitHub.

Note: this is for ADMIN accounts only. Student accounts are never created
here - they self-register via POST /api/auth/register, which derives their
username and email from their student number automatically (see
services/auth_service.py). Admins pick their own username since they
don't have a student number to derive one from.
"""
import getpass
from app import create_app
from database.connection import db
from database.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    print("--- Create admin account ---")
    full_name = input("Admin full name: ").strip()
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (min 8 chars): ")

    if User.query.filter_by(username=username).first():
        print(f"A user with username '{username}' already exists. Skipping.")
    else:
        admin = User(
            full_name=full_name,
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin account created for username '{username}'.")

    print("Done. Run schema.sql/seed.sql separately for services, queues, and service points.")
