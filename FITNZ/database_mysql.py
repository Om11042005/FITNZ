
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


def add_product(product_id, name, price, stock):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Insert into DB
        cur.execute(
            "INSERT INTO products (product_id, name, price, stock) VALUES (?, ?, ?, ?)",
            (product_id, name, float(price), int(stock))
        )
        conn.commit()

        # Fetch inserted record
        row = cur.execute(
            "SELECT product_id, name, price, stock FROM products WHERE product_id = ?",
            (product_id,)
        ).fetchone()

        if row:
            return Product(row[0], row[1], row[2], row[3])
        return None

    except Exception as e:
        conn.rollback()
        print("add_product error:", e)
        return None

    finally:
        conn.close()



def get_all_products():
    conn = get_conn()
    cur = conn.cursor()

    if USE_MYSQL and mysql:
        cur.execute("SELECT product_id, name, price, stock FROM products")
    else:
        cur.execute("SELECT product_id, name, price, stock FROM products")

    rows = cur.fetchall()
    conn.close()

    return [Product(r[0], r[1], r[2], r[3]) for r in rows]


def get_product_by_id(pid):
    conn = get_conn()
    cur = conn.cursor()

    if USE_MYSQL and mysql:
        cur.execute("SELECT product_id, name, price, stock FROM products WHERE product_id=%s OR id=%s", (pid, pid))
    else:
        cur.execute("SELECT product_id, name, price, stock FROM products WHERE product_id=? OR id=?", (pid, pid))

    row = cur.fetchone()
    conn.close()

    if row:
        return Product(row[0], row[1], row[2], row[3])

    return None


def update_product(pid, name, price, stock):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE products SET name=?, price=?, stock=? WHERE product_id=?",
            (name, float(price), int(stock), pid)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("update_product error:", e)
        return False
    finally:
        conn.close()


def delete_product(pid):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE product_id=?", (pid,))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        conn.close()



def get_all_users():
    conn = get_conn(); cur = conn.cursor()
    rows = cur.execute("SELECT * FROM users").fetchall(); conn.close()
    result = []
    for r in rows:
        role_val = r['role'] if 'role' in r.keys() else ''
        result.append(row_to_customer(r) if role_val and role_val.lower()=='customer' else row_to_employee(r))
    return result

def get_user_by_id(uid):
    conn = get_conn(); cur = conn.cursor()
    if USE_MYSQL and mysql:
        r = cur.execute("SELECT * FROM users WHERE id=%s OR user_id=%s OR username=%s",(uid,uid,uid,)).fetchone()
    else:
        r = cur.execute("SELECT * FROM users WHERE id=? OR user_id=? OR username=?", (uid, uid, uid)).fetchone()
    conn.close()
    if not r: return None
    role_val = r['role'] if 'role' in r.keys() else ''
    return row_to_customer(r) if role_val and role_val.lower()=='customer' else row_to_employee(r)

def delete_user_by_id(uid):
    try:
        conn = get_conn(); cur = conn.cursor()
        if USE_MYSQL and mysql:
            cur.execute("DELETE FROM users WHERE id=%s OR user_id=%s OR username=%s",(uid,uid,uid,))
        else:
            cur.execute("DELETE FROM users WHERE id=? OR user_id=? OR username=?", (uid, uid, uid))
        conn.commit(); conn.close(); return True
    except:
        return False

# ===============================================
# Code Owner: Sahil (US: Sale/Checkout Processing)
# Code Owner: Rajina (US: Discount Management - Membership tiers)
# ===============================================

def process_sale(customer_obj, cart, points_redeemed, student_discount_applied, delivery_date):
    try:
        conn = get_conn()
        cur = conn.cursor()

        now = datetime.now().isoformat(timespec='seconds')
        total = 0.0

        # Calculate totals
        for it in cart:
            pid = getattr(it, 'product_id', None)
            qty = getattr(it, 'qty', 1)
            price = getattr(it, 'price', 0)
            total += float(price) * int(qty)

        gst_total = round(total * 0.15, 2)
        grand_total = round(total + gst_total, 2)

        # Insert sale
        cur.execute(
            "INSERT INTO sales (datetime, user_id, customer_id, total, gst, delivery_date) VALUES (?,?,?,?,?,?)",
            (now, None, getattr(customer_obj, '_customer_id', None), grand_total, gst_total, str(delivery_date))
        )
        sale_id = cur.lastrowid

        # Insert sale lines
        for it in cart:
            pid = getattr(it, 'product_id', None)
            qty = getattr(it, 'qty', 1)
            price = getattr(it, 'price', 0)
            line_total = round((price * qty) * 1.15, 2)

            cur.execute(
                "INSERT INTO sale_lines (sale_id, product_id, qty, unit_price, line_total) VALUES (?,?,?,?,?)",
                (sale_id, pid, qty, price, line_total)
            )

            cur.execute(
                "UPDATE products SET stock = stock - ? WHERE product_id = ?",
                (qty, pid)
            )

        # ----- LOYALTY POINTS -----
        remaining_points = None
        if customer_obj and points_redeemed > 0:
            old_pts = getattr(customer_obj, 'loyalty_points', 0)
            remaining_points = max(0, old_pts - points_redeemed)

            cur.execute(
                "UPDATE customers SET loyalty_points = ? WHERE customer_id = ?",
                (remaining_points, customer_obj._customer_id)
            )

        conn.commit()
        conn.close()

        return True, remaining_points, gst_total, grand_total

    except Exception as e:
        print("process_sale error:", e)
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False, None, None, None
        
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

