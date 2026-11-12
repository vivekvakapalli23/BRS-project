#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper utility to automatically create the MySQL database for BookVerse AI.
Reads settings from .env file or environment variables.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
if not os.environ.get('DB_NAME'):
    load_dotenv(BASE_DIR.parent / '.env')

DB_NAME = os.environ.get('DB_NAME', 'bookverse_db').strip()
DB_USER = os.environ.get('DB_USER', 'root').strip()
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1').strip()
DB_PORT = int(os.environ.get('DB_PORT', '3306').strip())

def create_database():
    try:
        import pymysql
    except ImportError:
        print("[-] PyMySQL is not installed. Please run: pip install pymysql cryptography")
        return False

    pw_display = '*' * len(DB_PASSWORD) if DB_PASSWORD else '(empty)'
    print(f"[*] Attempting connection to MySQL at {DB_HOST}:{DB_PORT} as '{DB_USER}' (password: {pw_display})...")
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            charset='utf8mb4',
            connect_timeout=5
        )
        with connection.cursor() as cursor:
            sql = f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            cursor.execute(sql)
            print(f"[+] SUCCESS: MySQL database `{DB_NAME}` is ready!")
        connection.close()
        return True
    except pymysql.err.OperationalError as e:
        code = e.args[0] if e.args else None
        if code == 1045:
            print("\n[-] MySQL Access Denied (Error 1045):")
            print(f"    User '{DB_USER}' was rejected because your MySQL server requires a password.")
            print("    Please open the '.env' file in your project folder and set your MySQL password:")
            print("        DB_PASSWORD=your_actual_mysql_password")
            print("    Then re-run: python create_mysql_db.py\n")
        else:
            print(f"[-] MySQL Operational Error: {e}")
            print(f"    Please check if MySQL server is running on {DB_HOST}:{DB_PORT}.")
        return False
    except Exception as e:
        print(f"[-] Error: {e}")
        return False

if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)
