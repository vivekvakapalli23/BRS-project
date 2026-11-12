#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sync BookVerse AI database, tables, and seed data directly to MySQL.
"""

import os
import sys
import subprocess
from pathlib import Path

# Resolve project directories
ROOT_DIR = Path(__file__).resolve().parent
if (ROOT_DIR / 'manage.py').exists() and (ROOT_DIR / 'book_recommendation_system').exists():
    PROJECT_DIR = ROOT_DIR / 'book_recommendation_system'
else:
    PROJECT_DIR = ROOT_DIR

MANAGE_PY = PROJECT_DIR / 'manage.py'
ENV_FILE_ROOT = ROOT_DIR / '.env'
ENV_FILE_PROJECT = PROJECT_DIR / '.env'

def update_env_password(new_password):
    """Save the working MySQL password into .env files."""
    for env_path in [ENV_FILE_ROOT, ENV_FILE_PROJECT]:
        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        has_pw = False
        new_lines = []
        for line in lines:
            if line.strip().startswith('DB_PASSWORD='):
                new_lines.append(f"DB_PASSWORD={new_password}\n")
                has_pw = True
            elif line.strip().startswith('DB_ENGINE='):
                new_lines.append("DB_ENGINE=mysql\n")
            else:
                new_lines.append(line)

        if not has_pw:
            new_lines.append(f"DB_PASSWORD={new_password}\n")

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

def main():
    print("=" * 65)
    print("  BookVerse AI -> MySQL Database Setup & Migration Wizard")
    print("=" * 65)

    try:
        import pymysql
    except ImportError:
        print("[-] Installing pymysql driver...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pymysql", "cryptography"], check=True)
        import pymysql

    # Load existing password from .env if present
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE_PROJECT)
    load_dotenv(ENV_FILE_ROOT)

    db_user = os.environ.get('DB_USER', 'root').strip()
    db_host = os.environ.get('DB_HOST', '127.0.0.1').strip()
    db_port = int(os.environ.get('DB_PORT', '3306').strip())
    db_name = os.environ.get('DB_NAME', 'bookverse_db').strip()
    db_password = os.environ.get('DB_PASSWORD', '')

    # Test initial connection
    connected = False
    conn = None

    print(f"\n[*] Testing connection to MySQL at {db_host}:{db_port} as user '{db_user}'...")
    try:
        conn = pymysql.connect(host=db_host, user=db_user, password=db_password, port=db_port, connect_timeout=3)
        connected = True
        print("[+] Connected with current .env password!")
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1045:
            print(f"[-] Access denied with current password in .env.")
        else:
            print(f"[-] Connection failed: {e}")

    # Prompt user for password if not connected
    attempts = 0
    while not connected and attempts < 4:
        attempts += 1
        print("\n" + "-" * 60)
        user_pw = input(">> Enter your MySQL root password: ").strip()
        try:
            conn = pymysql.connect(host=db_host, user=db_user, password=user_pw, port=db_port, connect_timeout=3)
            connected = True
            db_password = user_pw
            print("[+] Connection SUCCESSFUL!")
            # Update .env
            update_env_password(db_password)
            os.environ['DB_PASSWORD'] = db_password
            os.environ['DB_ENGINE'] = 'mysql'
            print("[+] Saved password to .env file.")
        except Exception as err:
            print(f"[-] Failed with password '{user_pw}': {err}")

    if not connected:
        print("\n[-] Could not authenticate to MySQL. Please check your MySQL server credentials and retry.")
        sys.exit(1)

    # 1. Ensure bookverse_db exists in MySQL
    print(f"\n[*] 1/3: Ensuring database `{db_name}` exists in MySQL...")
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.close()
    print(f"    [+] Database `{db_name}` is ready!")

    # 2. Run Django migrations against MySQL
    print("\n[*] 2/3: Creating all Django tables in MySQL (Running migrate)...")
    env = os.environ.copy()
    env['DB_PASSWORD'] = db_password
    env['DB_ENGINE'] = 'mysql'

    res_migrate = subprocess.run(
        [sys.executable, str(MANAGE_PY), "migrate", "--noinput"],
        cwd=str(PROJECT_DIR),
        env=env
    )
    if res_migrate.returncode != 0:
        print("[-] Migration failed. Please inspect errors above.")
        sys.exit(1)
    print("    [+] All tables created successfully in MySQL!")

    # 3. Populate seed data & AI recommendation models
    print("\n[*] 3/3: Populating books, authors, genres & AI models (Running seed_data)...")
    res_seed = subprocess.run(
        [sys.executable, str(MANAGE_PY), "seed_data"],
        cwd=str(PROJECT_DIR),
        env=env
    )
    if res_seed.returncode != 0:
        print("[-] Seed data loading encountered an issue.")
    else:
        print("    [+] Seed data and AI models populated successfully in MySQL!")

    # Verify tables in MySQL
    print("\n" + "=" * 65)
    print("  VERIFYING MYSQL DATABASE TABLES & DATA:")
    print("=" * 65)
    try:
        verify_conn = pymysql.connect(
            host=db_host, user=db_user, password=db_password, database=db_name, port=db_port
        )
        with verify_conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"[+] Total Tables in `{db_name}`: {len(tables)}")

            if 'books_book' in tables:
                cursor.execute("SELECT COUNT(*) FROM books_book;")
                count = cursor.fetchone()[0]
                print(f"[+] Total Books in `books_book` table: {count}")

                cursor.execute("SELECT id, title, average_rating, publication_year FROM books_book LIMIT 5;")
                print("\n[*] Sample Books inside MySQL:")
                for b_id, title, rating, yr in cursor.fetchall():
                    print(f"    - [{b_id}] {title} ({yr}) -> Rating: {rating}/5.0")

        verify_conn.close()
        print("\n[+] SUCCESS! Everything is now stored and active inside MySQL!")
        print("    You can now switch to your MySQL monitor and run 'SHOW TABLES;' to see all tables!")
    except Exception as e:
        print(f"[-] Verification query warning: {e}")

if __name__ == '__main__':
    main()
