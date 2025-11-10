# File: FITNZ/database.py
import sqlite3
from datetime import date

from .models.customer import Customer, BronzeMember, SilverMember, GoldMember, StudentMember
from .models.employee import Employee
from .models.product import Product
from .models.sales import Sale

DATABASE_NAME = 'fitnz.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT UNIQUE NOT NULL, username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, role TEXT NOT NULL, name TEXT NOT NULL, contact TEXT, address TEXT,
            membership_level TEXT DEFAULT 'Standard', loyalty_points INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, employee_id TEXT, sale_date TEXT NOT NULL,
            delivery_date TEXT NOT NULL, total_amount REAL NOT NULL, FOREIGN KEY (customer_id) REFERENCES users (user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER NOT NULL, product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL, price_at_sale REAL NOT NULL, 
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''') # <-- NOTE: I've removed 'ON DELETE CASCADE' to be safe, will delete from sale_items manually

    if conn.execute("SELECT COUNT(id) FROM users").fetchone()[0] == 0:
        default_users = [
            ('E001', 'dev', 'dev123', 'Developer', 'Om Patel', 'dev@fit.nz', 'AIS Campus', 'Standard', 0),
            ('E002', 'manager', 'man123', 'Manager', 'Jane Doe', 'jane@fit.nz', 'AIS Campus', 'Standard', 0),
            ('E003', 'emp', 'emp123', 'Employee', 'John Smith', 'john@fit.nz', 'AIS Campus', 'Standard', 0),
            ('C101', 'alice', 'alice123', 'Customer', 'Alice Johnson', 'alice@example.com', '123 Queen St, Auckland', 'Gold', 500)
        ]
        cursor.executemany("INSERT INTO users (user_id, username, password, role, name, contact, address, membership_level, loyalty_points) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", default_users)
    
    if conn.execute("SELECT COUNT(id) FROM products").fetchone()[0] == 0:
        default_products = [
            ('RB001','Resistance Bands',35.00,50), 
            ('YM002','Yoga Mat',45.50,30), 
            ('DB003','Dumbbell Set',75.00,0), 
            ('PS004','Whey Protein',90.00,40)
        ]
        cursor.executemany("INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)", default_products)

    conn.commit()
    conn.close()

def _create_user_object(row):
    if not row: return None
    if row['role'] == 'Customer':
        cust = Customer(row['user_id'], row['name'], row['contact'], row['username'], row['password'])
        cust.address = row['address']; cust.loyalty_points = row['loyalty_points']
        level = row['membership_level']
        if level == "Bronze": return BronzeMember(cust)
        if level == "Silver": return SilverMember(cust)
        if level == "Gold": return GoldMember(cust)
        if level == "Student": return StudentMember(cust)
        return cust
    else:
        return Employee(row['user_id'], row['name'], row['role'], row['username'], row['password'])

def authenticate_user(username, password, role):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ? AND password = ? AND role = ?", (username, password, role)).fetchone()
        return _create_user_object(row)

def get_user_by_id(user_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return _create_user_object(row)

def add_user(name, contact, username, password, role, address):
    with get_db_connection() as conn:
        try:
            count = conn.execute('SELECT COUNT(id) FROM users').fetchone()[0]
            user_id = f"C{count+101}" if role == 'Customer' else f"E{count+101}"
            conn.execute("INSERT INTO users (user_id, username, password, role, name, contact, address) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, username, password, role, name, contact, address))
            conn.commit()
            return True
        except sqlite3.IntegrityError: return False

def get_all_products():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        return [Product(r['id'], r['name'], r['price'], r['stock']) for r in rows]

def get_product_by_id(product_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if row: return Product(row['id'], row['name'], row['price'], row['stock'])
        return None

def get_all_users():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
        return [_create_user_object(r) for r in rows]

def process_sale(customer, cart, points_redeemed, student_discount_applied, delivery_date):
    with get_db_connection() as conn:
        subtotal = sum(item.price for item in cart)
        final_total = subtotal
        if student_discount_applied: final_total -= subtotal * 0.20
        else: final_total -= subtotal * customer.get_discount_rate()
        if points_redeemed > 0: final_total -= points_redeemed * 0.10
        points_earned = int(final_total // 10)
        final_points = (customer.loyalty_points - points_redeemed) + points_earned
        conn.execute("UPDATE users SET loyalty_points = ? WHERE user_id = ?", (final_points, customer._customer_id))
        
        cursor = conn.execute("INSERT INTO sales (customer_id, sale_date, delivery_date, total_amount) VALUES (?, ?, ?, ?)", (customer._customer_id, date.today(), delivery_date, final_total))
        sale_id = cursor.lastrowid
        
        for item in cart:
            conn.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (?, ?, ?, ?)", (sale_id, item.product_id, 1, item.price))
            conn.execute("UPDATE products SET stock = stock - 1 WHERE id = ?", (item.product_id,))
        conn.commit()

def get_sales_for_customer(customer_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM sales WHERE customer_id = ? ORDER BY sale_date DESC", (customer_id,)).fetchall()

def get_all_sales():
    with get_db_connection() as conn:
        return conn.execute("SELECT s.id, s.sale_date, s.delivery_date, s.total_amount, u.name FROM sales s JOIN users u ON s.customer_id = u.user_id ORDER BY s.id DESC").fetchall()

def get_items_for_sale(sale_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT p.name, si.price_at_sale FROM sale_items si JOIN products p ON si.product_id = p.id WHERE si.sale_id = ?", (sale_id,)).fetchall()

def update_product_stock(product_id, new_quantity):
    with get_db_connection() as conn:
        conn.execute("UPDATE products SET stock = ? WHERE id = ?", (new_quantity, product_id))
        conn.commit()
    return True

def delete_user_by_id(user_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
    return True

def update_customer_membership(customer_id, new_level):
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET membership_level = ? WHERE user_id = ?", (new_level, customer_id))
        conn.commit()
    return True

def upgrade_to_student_membership(customer_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET membership_level = 'Student' WHERE user_id = ?", (customer_id,))
        conn.commit()
    return True

# --- NEW FUNCTION TO ADD PRODUCTS ---
def add_product(product_id, name, price, stock):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)", (product_id, name, price, stock))
            conn.commit()
        return True
    except sqlite3.IntegrityError: # This will catch a duplicate product_id
        print(f"Error: Product ID {product_id} already exists.")
        return False
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False

# --- NEW FUNCTION TO DELETE PRODUCTS ---
def delete_product(product_id):
    try:
        with get_db_connection() as conn:
            # We must delete from 'sale_items' first to avoid foreign key constraint errors
            conn.execute("DELETE FROM sale_items WHERE product_id = ?", (product_id,))
            # Now we can safely delete the product
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False