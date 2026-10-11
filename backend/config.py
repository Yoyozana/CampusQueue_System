import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load variables from the .env file — importing this module is enough,
# no need to call load_dotenv() again elsewhere.
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. Generate one with:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # --- MySQL ---
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "21778"))
    MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA","")  # path to ca.pem - required by hosts like Aiven

  
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # avoids "MySQL server has gone away" on free-tier hosts
        "pool_recycle": 280,
    }
    # Hosted MySQL providers like Aiven require SSL. If MYSQL_SSL_CA is
    # set, pass the certificate through to PyMySQL via connect_args so
    # the connection is actually encrypted and verified against it.
    # Left off entirely for plain local MySQL, where it isn't needed.
    if MYSQL_SSL_CA:
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"ssl": {"ca": MYSQL_SSL_CA}}

    # --- JWT ---
    # Explicit and separate from SECRET_KEY, rather than relying on
    # Flask-JWT-Extended's implicit fallback to SECRET_KEY.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is not set. Generate one with:\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    # Short-lived logins: the access token lasts 10 minutes and the
    # refresh token 8 hours. The browser also signs the user out after
    # 10 idle minutes and forgets the login when the tab is closed.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=10)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_TYPE = "Bearer"

    # --- CORS ---
    # Comma-separated list of allowed frontend origins, e.g.
    # "https://campusqueue.netlify.app,http://localhost:5500"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",")

    # --- Student email/username derivation (used by services/auth_service.py) ---
    STUDENT_EMAIL_DOMAIN = os.getenv("STUDENT_EMAIL_DOMAIN", "mywsu.ac.za")

    # --- Account lockout (services/auth_service.py) ---
    MAX_FAILED_LOGINS = int(os.getenv("MAX_FAILED_LOGINS", "5"))
    LOCKOUT_MINUTES = int(os.getenv("LOCKOUT_MINUTES", "15"))

    # --- Misc ---
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"