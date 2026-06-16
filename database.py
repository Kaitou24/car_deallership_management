

import sqlite3
import os
from car import Car


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            # Đặt file DB cùng thư mục với script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "dealership.db")
        self.db_path = db_path
        self.conn = None
        self.connect_db()


    def connect_db(self):
        """Kết nối tới SQLite và tạo bảng nếu chưa có."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._create_default_admin()

    def _create_tables(self):
        """Tạo các bảng Employees, Cars, Invoices."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                fullname TEXT NOT NULL,
                role TEXT DEFAULT 'staff'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                brand TEXT NOT NULL,
                year INTEGER NOT NULL,
                price REAL NOT NULL,
                status TEXT DEFAULT 'Còn hàng'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                price REAL NOT NULL,
                tax REAL NOT NULL,
                discount REAL DEFAULT 0,
                total REAL NOT NULL,
                FOREIGN KEY (car_id) REFERENCES Cars(id),
                FOREIGN KEY (employee_id) REFERENCES Employees(id)
            )
        """)

        self.conn.commit()

    def _create_default_admin(self):
        """Tạo tài khoản admin mặc định nếu chưa có."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Employees WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO Employees (username, password, fullname, role) VALUES (?, ?, ?, ?)",
                ("admin", "admin123", "Quản trị viên", "admin")
            )
            self.conn.commit()

    # ──────────────── Xác thực đăng nhập ────────────────

    def verify_login(self, username, password):
        """
        Kiểm tra thông tin đăng nhập.
        Trả về tuple (id, username, fullname, role) nếu đúng, None nếu sai.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, username, fullname, role FROM Employees WHERE username = ? AND password = ?",
            (username, password)
        )
        return cursor.fetchone()

    # ──────────────── Quản lý Xe (Cars) ────────────────

    def add_car(self, car: Car):
        """Thêm xe mới vào database."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO Cars (model, brand, year, price, status) VALUES (?, ?, ?, ?, ?)",
            (car.model, car.brand, car.year, car.price, car.status)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_car(self, car: Car):
        """Cập nhật thông tin xe."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Cars SET model = ?, brand = ?, year = ?, price = ?, status = ? WHERE id = ?",
            (car.model, car.brand, car.year, car.price, car.status, car.id)
        )
        self.conn.commit()

    def update_status(self, car_id, status):
        """Đổi trạng thái xe (Còn hàng / Đã bán)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE Cars SET status = ? WHERE id = ?",
            (status, car_id)
        )
        self.conn.commit()

    def delete_car(self, car_id):
        """Xóa xe khỏi database."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM Cars WHERE id = ?", (car_id,))
        self.conn.commit()

    def get_all_cars(self):
        """Lấy danh sách tất cả xe, trả về list[Car]."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, model, brand, year, price, status FROM Cars ORDER BY id DESC")
        rows = cursor.fetchall()
        return [Car.from_row(row) for row in rows]

    def get_car_by_id(self, car_id):
        """Lấy thông tin 1 xe theo ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, model, brand, year, price, status FROM Cars WHERE id = ?", (car_id,))
        row = cursor.fetchone()
        return Car.from_row(row) if row else None

    def search_cars(self, keyword, status_filter=None):
        """Tìm kiếm xe theo keyword (model/brand) và lọc trạng thái."""
        cursor = self.conn.cursor()
        query = "SELECT id, model, brand, year, price, status FROM Cars WHERE (model LIKE ? OR brand LIKE ?)"
        params = [f"%{keyword}%", f"%{keyword}%"]

        if status_filter and status_filter != "Tất cả":
            query += " AND status = ?"
            params.append(status_filter)

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [Car.from_row(row) for row in rows]

    # ──────────────── Quản lý Hóa đơn (Invoices) ────────────────

    def add_invoice(self, car_id, employee_id, customer_name, sale_date, price, tax, discount, total):
        """Lưu hóa đơn bán xe."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO Invoices (car_id, employee_id, customer_name, sale_date, price, tax, discount, total)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (car_id, employee_id, customer_name, sale_date, price, tax, discount, total)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_all_invoices(self):
        """Lấy danh sách tất cả hóa đơn kèm thông tin xe và nhân viên."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.id, c.brand || ' ' || c.model AS car_name, e.fullname,
                   i.customer_name, i.sale_date, i.price, i.tax, i.discount, i.total
            FROM Invoices i
            JOIN Cars c ON i.car_id = c.id
            JOIN Employees e ON i.employee_id = e.id
            ORDER BY i.id DESC
        """)
        return cursor.fetchall()

    # ──────────────── Thống kê ────────────────

    def get_stats(self):
        """Trả về thống kê: tổng xe, xe còn hàng, xe đã bán."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Cars")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Cars WHERE status = 'Còn hàng'")
        available = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Cars WHERE status = 'Đã bán'")
        sold = cursor.fetchone()[0]
        return {"total": total, "available": available, "sold": sold}

    def close(self):
        """Đóng kết nối database."""
        if self.conn:
            self.conn.close()
