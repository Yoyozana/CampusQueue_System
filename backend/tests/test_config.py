from config import Config

print("SQLALCHEMY_DATABASE_URI:", Config.SQLALCHEMY_DATABASE_URI)
print("CORS_ORIGINS:", Config.CORS_ORIGINS)
print("DEBUG:", Config.DEBUG)
print("STUDENT_EMAIL_DOMAIN:", Config.STUDENT_EMAIL_DOMAIN)
print("PASS: config loaded successfully")
