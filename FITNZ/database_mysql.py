
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


# Sahil Part


# Rajina:
def update_customer_membership(customer_id, new_tier):
    try:
        conn = get_conn(); cur = conn.cursor()
        if USE_MYSQL and mysql:
            cur.execute("UPDATE users SET membership_level=%s WHERE user_id=%s OR username=%s OR id=%s", (new_tier, customer_id, customer_id, customer_id))
        else:
            cur.execute("UPDATE users SET membership_level=? WHERE user_id=? OR username=? OR id=?", (new_tier, customer_id, customer_id, customer_id))
        conn.commit(); conn.close(); return True
    except Exception as e:
        return False
# Rajina:
def upgrade_to_student_membership(customer_id):
    return update_customer_membership(customer_id, "Student")

# Rajina:
def get_all_sales():
    try:
        conn = get_conn()
        cur = conn.cursor()

        rows = cur.execute("""
            SELECT s.id, s.datetime, s.customer_id, s.total, s.gst, s.delivery_date,
                   c.name AS customer_name
            FROM sales s
            LEFT JOIN customers c ON c.customer_id = s.customer_id
            ORDER BY s.datetime DESC
        """).fetchall()

        data = []
        for r in rows:
            data.append({
                "sale_id": r[0],
                "datetime": r[1],
                "customer": r[6] or "Walk-in",
                "total": r[3],
                "gst": r[4],
                "delivery_date": r[5]
            })

        conn.close()
        return data
    except Exception as e:
        print("get_all_sales error:", e)
        return []

