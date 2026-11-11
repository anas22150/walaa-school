# database.py
import sqlite3
import shutil
import os
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name='scanner.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                year TEXT NOT NULL,
                fee REAL DEFAULT 0,
                phone TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                month INTEGER NOT NULL,
                year_num INTEGER NOT NULL,
                paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, month, year_num)
            )
        ''')
        self.conn.commit()

    def export_db(self, target_path):
        try:
            self.conn.commit()
            shutil.copy2(self.db_name, target_path)
            return True, target_path
        except Exception as e:
            return False, str(e)

    def import_db(self, source_path):
        try:
            src = sqlite3.connect(source_path)
            src.row_factory = sqlite3.Row
            sc = src.cursor()
            n_students = 0
            n_payments = 0
            errors = []
            id_map = {}
            try:
                sc.execute("SELECT id, code, name, year, fee, phone FROM students")
                for row in sc.fetchall():
                    try:
                        old_id = row['id']
                        code = row['code']
                        existing = self.get_student_by_code(code)
                        if existing:
                            id_map[old_id] = existing['id']
                            continue
                        self.cursor.execute(
                            'INSERT INTO students (code, name, year, fee, phone) VALUES (?,?,?,?,?)',
                            (code, row['name'], row['year'], row['fee'] or 0, row['phone'] or '')
                        )
                        id_map[old_id] = self.cursor.lastrowid
                        n_students += 1
                    except Exception as e:
                        errors.append(f"طالب: {e}")
            except Exception as e:
                errors.append(f"قراءة الطلاب: {e}")
            try:
                sc.execute("SELECT student_id, amount, month, year_num FROM payments")
                for row in sc.fetchall():
                    try:
                        new_sid = id_map.get(row['student_id'])
                        if not new_sid:
                            continue
                        existing = self.cursor.execute(
                            'SELECT id FROM payments WHERE student_id=? AND month=? AND year_num=?',
                            (new_sid, row['month'], row['year_num'])
                        ).fetchone()
                        if existing:
                            continue
                        self.cursor.execute(
                            'INSERT INTO payments (student_id, amount, month, year_num) VALUES (?,?,?,?)',
                            (new_sid, row['amount'], row['month'], row['year_num'])
                        )
                        n_payments += 1
                    except Exception as e:
                        errors.append(f"دفعة: {e}")
            except Exception as e:
                errors.append(f"قراءة المدفوعات: {e}")
            self.conn.commit()
            src.close()
            return True, f"تم استيراد {n_students} طالب و {n_payments} دفعة", errors
        except Exception as e:
            return False, f"خطأ: {e}", []

    def add_student(self, name, year, fee, phone):
        code = f"STU-{int(datetime.now().timestamp() * 1000) % 1000000:06d}"
        self.cursor.execute(
            'INSERT INTO students (code, name, year, fee, phone) VALUES (?, ?, ?, ?, ?)',
            (code, name, year, fee, phone)
        )
        self.conn.commit()
        return code

    def get_all_students(self):
        self.cursor.execute('SELECT * FROM students ORDER BY year, name')
        return [dict(row) for row in self.cursor.fetchall()]

    def get_student_by_code(self, code):
        self.cursor.execute('SELECT * FROM students WHERE code = ?', (code,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_student_by_id(self, student_id):
        self.cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def update_student(self, student_id, name, year, fee, phone):
        self.cursor.execute(
            'UPDATE students SET name=?, year=?, fee=?, phone=? WHERE id=?',
            (name, year, fee, phone, student_id)
        )
        self.conn.commit()

    def delete_student(self, student_id):
        self.cursor.execute('DELETE FROM payments WHERE student_id = ?', (student_id,))
        self.cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        self.conn.commit()

    def count_students(self):
        self.cursor.execute('SELECT COUNT(*) as c FROM students')
        return self.cursor.fetchone()['c']

    def get_payments_for_student(self, student_id, year_num):
        self.cursor.execute(
            'SELECT * FROM payments WHERE student_id = ? AND year_num = ?',
            (student_id, year_num)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def toggle_payment(self, student_id, month, year_num, amount):
        self.cursor.execute(
            'SELECT id FROM payments WHERE student_id=? AND month=? AND year_num=?',
            (student_id, month, year_num)
        )
        existing = self.cursor.fetchone()
        if existing:
            self.cursor.execute('DELETE FROM payments WHERE id=?', (existing['id'],))
            self.conn.commit()
            return False
        else:
            self.cursor.execute(
                'INSERT INTO payments (student_id, amount, month, year_num) VALUES (?, ?, ?, ?)',
                (student_id, amount, month, year_num)
            )
            self.conn.commit()
            return True

    def get_paid_student_ids(self, month, year_num):
        self.cursor.execute(
            'SELECT student_id FROM payments WHERE month=? AND year_num=?',
            (month, year_num)
        )
        return {row['student_id'] for row in self.cursor.fetchall()}

    def get_all_years(self):
        self.cursor.execute('SELECT DISTINCT year FROM students ORDER BY year')
        return [row['year'] for row in self.cursor.fetchall()]
