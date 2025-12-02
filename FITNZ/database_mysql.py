
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
# ===============================================
# Code Owner: Imran (US: Admin/Reports - Core DB Access & Management)
# ===============================================

def get_conn():
    if USE_MYSQL and mysql:
        # Build connection from env
        conn = mysql.connect(
            host=config.get("MYSQL_HOST","127.0.0.1"),
            port=int(config.get("MYSQL_PORT","3306")),
            user=config.get("MYSQL_USER","root"),
            password=config.get("MYSQL_PASSWORD",""),
            database=config.get("MYSQL_DB","fitnz_db"),
            autocommit=False
        )
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

# Model mapping helpers: delayed imports to avoid circular
def row_to_product(row):
    if row is None: return None
    try:
        from .models.product import Product
    except Exception:
        from models.product import Product
    # support sqlite3.Row or dict or SimpleNamespace
    if hasattr(row, "keys"):
        pid = row['product_id'] if 'product_id' in row.keys() else (row['id'] if 'id' in row.keys() else "")
        name = row['name'] if 'name' in row.keys() else ""
        price = float(row['price']) if 'price' in row.keys() else 0.0
        stock = int(row['stock']) if 'stock' in row.keys() else 0
    elif isinstance(row, dict):
        pid = row.get('product_id') or row.get('id') or ""
        name = row.get('name') or ""
        price = float(row.get('price') or 0.0)
        stock = int(row.get('stock') or 0)
    else:
        # SimpleNamespace or model object
        pid = getattr(row, "product_id", getattr(row, "id", ""))
        name = getattr(row, "name", "")
        price = float(getattr(row, "price", 0.0))
        stock = int(getattr(row, "stock", 0))
    return Product(str(pid), name, price, stock)

def row_to_customer(row):
    if row is None: return None
    try:
        from .models.customer import Customer
    except Exception:
        from models.customer import Customer
    # extract fields safely
    if hasattr(row, "keys"):
        user_id = row['user_id'] if 'user_id' in row.keys() else (row['customer_id'] if 'customer_id' in row.keys() else "")
        name = row['name'] if 'name' in row.keys() else ""
        contact = row['contact'] if 'contact' in row.keys() else (row['email'] if 'email' in row.keys() else "")
        username = row['username'] if 'username' in row.keys() else ""
        password = row['password'] if 'password' in row.keys() else ""
        loyalty = int(row['loyalty_points']) if 'loyalty_points' in row.keys() and row['loyalty_points'] is not None else 0
        membership = row['membership_level'] if 'membership_level' in row.keys() else (row['tier'] if 'tier' in row.keys() else 'Standard')
        address = row['address'] if 'address' in row.keys() else ""
    elif isinstance(row, dict):
        user_id = row.get('user_id') or row.get('customer_id') or ""
        name = row.get('name') or ""
        contact = row.get('contact') or row.get('email') or ""
        username = row.get('username') or ""
        password = row.get('password') or ""
        loyalty = int(row.get('loyalty_points') or 0)
        membership = row.get('membership_level') or row.get('tier') or 'Standard'
        address = row.get('address') or ""
    else:
        user_id = getattr(row, "user_id", getattr(row, "customer_id", ""))
        name = getattr(row, "name", "")
        contact = getattr(row, "contact", getattr(row, "email", ""))
        username = getattr(row, "username", "")
        password = getattr(row, "_password", getattr(row, "password", ""))
        loyalty = int(getattr(row, "loyalty_points", 0))
        membership = getattr(row, "membership_level", getattr(row, "membership", "Standard"))
        address = getattr(row, "address", "")
    cust = Customer(user_id, name, contact, username, password)
    cust.loyalty_points = loyalty
    cust.membership_level = membership
    cust.address = address
    return cust

def row_to_employee(row):
    if row is None: return None
    try:
        from .models.employee import Employee
    except Exception:
        from models.employee import Employee
    if hasattr(row, "keys"):
        eid = row['user_id'] if 'user_id' in row.keys() else ""
        name = row['name'] if 'name' in row.keys() else ""
        role = row['role'] if 'role' in row.keys() else ""
        username = row['username'] if 'username' in row.keys() else ""
        password = row['password'] if 'password' in row.keys() else ""
    elif isinstance(row, dict):
        eid = row.get('user_id') or ""
        name = row.get('name') or ""
        role = row.get('role') or ""
        username = row.get('username') or ""
        password = row.get('password') or ""
    else:
        eid = getattr(row, "user_id", "")
        name = getattr(row, "name", "")
        role = getattr(row, "role", "")
        username = getattr(row, "username", "")
        password = getattr(row, "_password", getattr(row, "password", ""))
    return Employee(eid, name, role, username, password)

# ------------------------- Database functions -------------------------

def setup_database():
    conn = get_conn(); cur = conn.cursor()
    # Use different SQL for MySQL vs SQLite if needed
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        name TEXT,
        contact TEXT,
        address TEXT,
        membership_level TEXT DEFAULT 'Standard',
        loyalty_points INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE,
        sku TEXT,
        name TEXT,
        description TEXT,
        price REAL,
        stock INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        name TEXT,
        email TEXT,
        phone TEXT,
        tier TEXT DEFAULT 'Bronze',
        loyalty_points INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT,
        user_id TEXT,
        customer_id TEXT,
        total REAL,
        gst REAL,
        delivery_date TEXT
    );
    CREATE TABLE IF NOT EXISTS sale_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER,
        product_id TEXT,
        qty INTEGER,
        unit_price REAL,
        line_total REAL
    );
    """)
    # seed users & products
    cur.execute("SELECT COUNT(*) FROM users"); cnt = cur.fetchone()[0]
    if cnt == 0:
        defaults = [
            ('E001','dev','dev123','Developer','Om Patel','dev@fit.nz','AIS Campus','Standard',0),
            ('E002','manager','man123','Manager','Jane Doe','jane@fit.nz','AIS Campus','Standard',0),
            ('E003','emp','emp123','Employee','John Smith','john@fit.nz','AIS Campus','Standard',0),
            ('C101','alice','alice123','Customer','Alice','alice@example.com','123 Queen St, Auckland','Gold',500)
        ]
        for u in defaults:
            cur.execute("INSERT INTO users (user_id, username, password, role, name, contact, address, membership_level, loyalty_points) VALUES (?,?,?,?,?,?,?,?,?)", u)
    cur.execute("SELECT COUNT(*) FROM products"); pcount = cur.fetchone()[0]
    if pcount == 0:
        products = [
            ('P001','BND001','Resistance Band - Light','Light resistance band, 1m',12.0,50),
            ('P002','MAT001','Yoga Mat - Eco','Eco-friendly yoga mat',30.0,20),
            ('P003','WGT001','Dumbbell 5kg','Cast iron dumbbell 5kg',40.0,10),
            ('P004','PRT001','Protein Powder 1kg','Whey protein 1kg',80.0,25)
        ]
        for p in products:
            cur.execute("INSERT INTO products (product_id, sku, name, description, price, stock) VALUES (?,?,?,?,?,?)", p)
    conn.commit(); conn.close()



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

