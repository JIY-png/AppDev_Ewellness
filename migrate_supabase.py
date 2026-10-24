"""
Supabase Schema Migration & Verification Tool
==============================================
This tool verifies table status and can apply `supabase_schema.sql`
directly to your Supabase PostgreSQL database if your database connection
or password is provided.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def check_tables():
    print("=" * 60)
    print("Checking Supabase Tables Status...")
    print("=" * 60)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] Missing SUPABASE_URL or SUPABASE_KEY in .env file.")
        return False

    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client: {e}")
        return False

    tables = ["patients", "records", "admin_users", "access_logs"]
    all_ok = True

    for table in tables:
        try:
            res = supabase.table(table).select("*").limit(1).execute()
            print(f"  [OK] Table '{table}' exists (current row count preview: {len(res.data or [])})")
        except Exception as e:
            err = str(e)
            if "PGRST205" in err or "Could not find the table" in err:
                print(f"  [MISSING] Table '{table}' does NOT exist yet in Supabase schema cache.")
            else:
                print(f"  [ERROR] Table '{table}' check error: {err}")
            all_ok = False

    print("=" * 60)
    if all_ok:
        print("[SUCCESS] All required database tables exist in Supabase!")
    else:
        print("[NOTICE] One or more tables are missing.")
        print("To migrate, run the contents of 'supabase_schema.sql' in:")
        print("  Supabase Dashboard -> SQL Editor -> New Query -> Run")
        print("Or run this script with --password <your_db_password>")
    print("=" * 60)
    return all_ok

def apply_migration(db_password=None, db_url=None):
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supabase_schema.sql")
    if not os.path.exists(schema_path):
        print(f"[ERROR] Schema file not found at {schema_path}")
        return False

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        import psycopg2
    except ImportError:
        print("[ERROR] psycopg2-binary not installed. Run: pip install psycopg2-binary")
        return False

    conn = None
    try:
        if db_url:
            print(f"Connecting using database URL...")
            conn = psycopg2.connect(db_url)
        elif db_password:
            # Extract project ref from SUPABASE_URL
            # e.g. https://nzctsbioowpbnaisbcky.supabase.co -> nzctsbioowpbnaisbcky
            project_ref = SUPABASE_URL.replace("https://", "").replace("http://", "").split(".")[0]
            
            # Try connection via direct or pooler hosts
            hosts = [
                (f"db.{project_ref}.supabase.co", 5432, "postgres", "postgres"),
                ("aws-0-ap-southeast-1.pooler.supabase.com", 6543, f"postgres.{project_ref}", "postgres"),
                ("aws-0-us-east-1.pooler.supabase.com", 6543, f"postgres.{project_ref}", "postgres")
            ]
            
            connected = False
            for host, port, user, dbname in hosts:
                try:
                    print(f"Attempting connection to {host}:{port} as {user}...")
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        dbname=dbname,
                        user=user,
                        password=db_password,
                        connect_timeout=5
                    )
                    connected = True
                    print(f"[OK] Connected successfully to {host}!")
                    break
                except Exception as ex:
                    print(f"  Connection to {host} failed: {ex}")
            
            if not connected:
                print("[ERROR] Could not connect to Supabase PostgreSQL using provided password.")
                return False
        else:
            print("[ERROR] Please provide --password or --db-url")
            return False

        print("Executing supabase_schema.sql...")
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("[SUCCESS] Schema migration completed successfully!")
        conn.close()
        return check_tables()

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        if conn:
            conn.close()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supabase migration & verification script")
    parser.add_argument("--check", action="store_true", help="Check if tables exist in Supabase")
    parser.add_argument("--password", type=str, help="Supabase database password")
    parser.add_argument("--db-url", type=str, help="Full PostgreSQL connection string")
    args = parser.parse_args()

    if args.password or args.db_url:
        apply_migration(db_password=args.password, db_url=args.db_url)
    else:
        check_tables()
