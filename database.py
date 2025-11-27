# database.py
import mysql.connector
from config import DB_CONFIG


def connect_db(with_database=True):
    """
    Open a MySQL connection using settings from config.DB_CONFIG.
    If with_database=False, connects only to the server (used to create DB).
    """
    if with_database:
        return mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
        )
    else:
        return mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
        )


def create_database():
    """
    Creates the FIT NZ database and all tables if they do not exist.
    This is called once at import time.
    """
    server_conn = connect_db(with_database=False)
    cur = server_conn.cursor()

    # Create DB
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']};")
    cur.execute(f"USE {DB_CONFIG['database']};")

    # CUSTOMERS TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name   VARCHAR(120) NOT NULL,
            email       VARCHAR(150) UNIQUE NOT NULL,
            password    VARCHAR(255) NOT NULL,
            phone       VARCHAR(20),
            address     TEXT,
            login_count INT DEFAULT 0,
            total_spent DECIMAL(12,2) DEFAULT 0,
            last_login  TIMESTAMP NULL DEFAULT NULL
        );
        """
    )

    # EQUIPMENT CATEGORY TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS equipment_category (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100) NOT NULL,
            description TEXT
        );
        """
    )

    # EQUIPMENT TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS equipment (
            equipment_id INT AUTO_INCREMENT PRIMARY KEY,
            name         VARCHAR(150) NOT NULL,
            brand        VARCHAR(100),
            description  TEXT,
            price        DECIMAL(10,2) NOT NULL,
            stock        INT DEFAULT 0,
            category_id  INT,
            difficulty   ENUM('Beginner','Intermediate','Advanced') DEFAULT 'Beginner',
            image_path   VARCHAR(255),
            is_active    TINYINT(1) DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES equipment_category(category_id)
                ON DELETE SET NULL
        );
        """
    )

    # CART TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cart (
            cart_id      INT AUTO_INCREMENT PRIMARY KEY,
            customer_id  INT NOT NULL,
            equipment_id INT NOT NULL,
            quantity     INT DEFAULT 1,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
            FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
        );
        """
    )

    # ORDERS TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id     INT AUTO_INCREMENT PRIMARY KEY,
            customer_id  INT NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            order_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status       ENUM('Pending','Processing','Shipped','Completed','Cancelled')
                         DEFAULT 'Pending',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        );
        """
    )

    # ORDER ITEMS TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            item_id      INT AUTO_INCREMENT PRIMARY KEY,
            order_id     INT NOT NULL,
            equipment_id INT NOT NULL,
            quantity     INT NOT NULL,
            unit_price   DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
        );
        """
    )

    # PAYMENTS TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id     INT AUTO_INCREMENT PRIMARY KEY,
            order_id       INT NOT NULL,
            payment_method ENUM('Card','Bank Transfer','Cash','AfterPay') DEFAULT 'Card',
            amount         DECIMAL(10,2) NOT NULL,
            payment_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status         ENUM('Pending','Completed','Failed','Refunded') DEFAULT 'Completed',
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
        );
        """
    )

    # RATINGS TABLE
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS equipment_ratings (
            rating_id    INT AUTO_INCREMENT PRIMARY KEY,
            customer_id  INT NOT NULL,
            equipment_id INT NOT NULL,
            rating       TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment      TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_customer_equipment (customer_id, equipment_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
            FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
        );
        """
    )

    server_conn.commit()
    cur.close()
    server_conn.close()
    print("FIT NZ database and tables created/updated successfully!")


# ---------- Analytics & helper functions ----------

def increment_login_counter(customer_id):
    db = connect_db()
    cur = db.cursor()
    try:
        cur.execute(
            """
            UPDATE customers
            SET login_count = COALESCE(login_count,0) + 1,
                last_login  = NOW()
            WHERE customer_id=%s
            """,
            (customer_id,),
        )
        db.commit()
    finally:
        db.close()


def record_order_effects(order_id):
    """Adds order.total_amount to the customer's total_spent."""
    db = connect_db()
    cur = db.cursor()
    try:
        cur.execute(
            "SELECT customer_id, total_amount FROM orders WHERE order_id=%s",
            (order_id,),
        )
        row = cur.fetchone()
        if row:
            customer_id, total_amount = row
            cur.execute(
                """
                UPDATE customers
                SET total_spent = COALESCE(total_spent,0) + %s
                WHERE customer_id=%s
                """,
                (total_amount, customer_id),
            )
            db.commit()
    finally:
        db.close()


def add_or_update_rating(customer_id, equipment_id, rating, comment=None):
    if rating < 1 or rating > 5:
        raise ValueError("rating must be between 1 and 5")

    db = connect_db()
    cur = db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO equipment_ratings (customer_id, equipment_id, rating, comment)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                rating = VALUES(rating),
                comment = VALUES(comment),
                created_at = CURRENT_TIMESTAMP
            """,
            (customer_id, equipment_id, rating, comment),
        )
        db.commit()
    finally:
        db.close()


def get_equipment_rating(equipment_id):
    """Returns (average_rating, ratings_count) for a piece of equipment."""
    db = connect_db()
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT COALESCE(AVG(rating),0), COUNT(*)
            FROM equipment_ratings
            WHERE equipment_id=%s
            """,
            (equipment_id,),
        )
        avg_rating, count = cur.fetchone()
        return float(avg_rating or 0), int(count or 0)
    finally:
        db.close()


def get_customer_stats(customer_id):
    """Returns dict with total_spent, login_count, last_login."""
    db = connect_db()
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT COALESCE(total_spent,0),
                   COALESCE(login_count,0),
                   last_login
            FROM customers
            WHERE customer_id=%s
            """,
            (customer_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"total_spent": 0.0, "login_count": 0, "last_login": None}
        total_spent, login_count, last_login = row
        return {
            "total_spent": float(total_spent or 0),
            "login_count": int(login_count or 0),
            "last_login": last_login,
        }
    finally:
        db.close()


def get_most_sold_equipment(limit=10):
    """Returns list of (equipment_id, name, total_sold) sorted desc by sold quantity."""
    db = connect_db()
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT e.equipment_id, e.name, COALESCE(SUM(oi.quantity), 0) AS total_sold
            FROM equipment e
            LEFT JOIN order_items oi ON oi.equipment_id = e.equipment_id
            GROUP BY e.equipment_id, e.name
            ORDER BY total_sold DESC, e.equipment_id ASC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()
    finally:
        db.close()


def get_least_sold_equipment(limit=10):
    """Returns list of (equipment_id, name, total_sold) sorted asc (includes zeros)."""
    db = connect_db()
    cur = db.cursor()
    try:
        cur.execute(
            """
            SELECT e.equipment_id, e.name, COALESCE(SUM(oi.quantity), 0) AS total_sold
            FROM equipment e
            LEFT JOIN order_items oi ON oi.equipment_id = e.equipment_id
            GROUP BY e.equipment_id, e.name
            ORDER BY total_sold ASC, e.equipment_id ASC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()
    finally:
        db.close()


# auto-create DB & tables when module is imported
create_database()
