
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


# Imran Part



# ===============================================
# Code Owner: Om (US: Registration/Login Logic)
# ===============================================

def authenticate_user(username, password, role=None):
    conn = get_conn(); cur = conn.cursor()
    if USE_MYSQL and mysql:
        if role:
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role=%s", (username, password, role))
        else:
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        r = cur.fetchone(); conn.close(); return row_to_employee(r) if r and r.get('role','').lower()!='customer' else row_to_customer(r)
    else:
        if role:
            cur.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password, role))
        else:
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        r = cur.fetchone(); conn.close()
        if not r: return None
        # role column may contain 'Customer' or others
        role_val = r['role'] if 'role' in r.keys() else ''
        if role_val and role_val.lower() == 'customer':
            return row_to_customer(r)
        else:
            return row_to_employee(r)

def add_user(name, contact, username, password, role, address):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); cnt = cur.fetchone()[0] + 1
        user_id = f"U{cnt:03d}"
        if USE_MYSQL and mysql:
            cur.execute("INSERT INTO users (user_id, username, password, role, name, contact, address) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (user_id, username, password, role, name, contact, address))
        else:
            cur.execute("INSERT INTO users (user_id, username, password, role, name, contact, address) VALUES (?,?,?,?,?,?,?)",
                        (user_id, username, password, role, name, contact, address))
        conn.commit()
        # return created user object
        r = cur.execute("SELECT * FROM users WHERE user_id=?",(user_id,)).fetchone() if not (USE_MYSQL and mysql) else cur.execute("SELECT * FROM users WHERE user_id=%s",(user_id,)).fetchone()
        return row_to_employee(r) if r and (r['role'] if 'role' in r.keys() else '') and (r['role'].lower()!='customer') else row_to_customer(r)
    except Exception as e:
        conn.rollback()
        return None
    finally:
        conn.close()
