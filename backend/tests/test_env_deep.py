import os

# --- Check 1: is JWT_SECRET_KEY already set in the raw OS environment,
# BEFORE we even touch dotenv? python-dotenv does NOT override an
# existing environment variable by default, so if this is already set
# to something (even an empty string), it will silently win over
# whatever is in your .env file.
print("=== BEFORE load_dotenv() ===")
print("Raw OS env JWT_SECRET_KEY:", repr(os.environ.get("JWT_SECRET_KEY")))
print("Raw OS env SECRET_KEY:", repr(os.environ.get("SECRET_KEY")))

# --- Check 2: which .env file is dotenv actually finding? ---
from dotenv import find_dotenv, load_dotenv
found_path = find_dotenv()
print()
print("=== .env file dotenv is using ===")
print("Path found:", repr(found_path))

# --- Check 3: read the .env file directly, byte by byte, so hidden
# characters (invisible spaces, BOM, smart quotes from copy-paste)
# become visible instead of invisible.
print()
print("=== Raw lines in that .env file ===")
with open(found_path, "rb") as f:
    for i, line in enumerate(f.readlines(), start=1):
        print(f"Line {i}: {line!r}")

# --- Check 4: now actually load it and see the result ---
load_dotenv(override=True)  # force override, just for this diagnostic
print()
print("=== AFTER load_dotenv(override=True) ===")
print("JWT_SECRET_KEY:", repr(os.getenv("JWT_SECRET_KEY")))
print("SECRET_KEY:", repr(os.getenv("SECRET_KEY")))
