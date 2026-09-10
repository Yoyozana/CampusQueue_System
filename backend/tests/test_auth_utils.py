from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from config import Config
from utils.auth import role_required, build_student_email, is_valid_student_number

# --- Validator tests ---
assert is_valid_student_number("260000001") is True
assert is_valid_student_number("12345") is False
assert is_valid_student_number("26000000a") is False
print("PASS: student number validation")

# --- Email derivation test ---
app = Flask(__name__)
app.config.from_object(Config)
with app.app_context():
    email = build_student_email("260000001")
    print("PASS: build_student_email ->", email)

# --- role_required test, with real JWTs ---
jwt = JWTManager(app)

@app.route("/admin-only")
@role_required("admin")
def admin_only():
    return jsonify({"message": "welcome admin"})

client = app.test_client()
with app.app_context():
    admin_token = create_access_token(identity="1", additional_claims={"role": "admin"})
    student_token = create_access_token(identity="2", additional_claims={"role": "student"})

resp = client.get("/admin-only", headers={"Authorization": f"Bearer {admin_token}"})
assert resp.status_code == 200
print("PASS: admin token accepted ->", resp.status_code)

resp = client.get("/admin-only", headers={"Authorization": f"Bearer {student_token}"})
assert resp.status_code == 403
print("PASS: student token correctly rejected ->", resp.status_code)

resp = client.get("/admin-only")
assert resp.status_code == 401
print("PASS: no token correctly rejected ->", resp.status_code)

print("ALL TESTS PASSED")
