from dotenv import load_dotenv
import os

load_dotenv()

print("SECRET_KEY:", repr(os.getenv("SECRET_KEY")))
print("JWT_SECRET_KEY:", repr(os.getenv("JWT_SECRET_KEY")))
