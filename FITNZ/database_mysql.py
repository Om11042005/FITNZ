
import os, sqlite3
from datetime import datetime
from types import SimpleNamespace
from .models.product import Product

BASE = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "fitnz.sqlite3")
ENV_PATH = os.path.join(BASE, "database.env")

# Read simple env file
config = {}
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                k,v=line.split("=",1); config[k.strip()]=v.strip()

USE_MYSQL = config.get("DATABASE_ENGINE","").lower() == "mysql"

# Optional MySQL connector. If not present, will fallback to sqlite.
mysql = None
if USE_MYSQL:
    try:
        import mysql.connector as mysql
    except Exception as e:
        mysql = None
