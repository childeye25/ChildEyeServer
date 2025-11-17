# ============================================================
# 🔌 Database Connection Module
# ============================================================

import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",       # <-- ضعي الباسورد إذا عندك
            database="child_eye"
        )

        if conn.is_connected():
            return conn

    except Error as e:
        print("❌ Database Connection Error:", e)
        return None
