from config import Config
from sqlalchemy.engine import make_url

url = make_url(Config.SQLALCHEMY_DATABASE_URI)
print("Parsed host:", url.host)
print("Parsed database:", url.database)
