
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load env variables from root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logging.error("Supabase credentials missing!")
    exit(1)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
except Exception as e:
    logging.error(f"Failed to init Supabase: {e}")
    exit(1)

def run_migration():
    # Read the SQL file
    sql_file_path = os.path.join(os.path.dirname(__file__), 'add_vuln_columns.sql')
    try:
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
    except FileNotFoundError:
        logging.error(f"Migration file not found: {sql_file_path}")
        return

    logging.info("Applying migration...")
    
    # We can't execute raw SQL directly with the JS/Python client usually unless we use an RPC
    # or if we are using the Postgres connection directly.
    # However, sometimes we can use the `rpc` function if a registered function exists to run sql.
    # OR we can try to use a library like `psycopg2` if we had the connection string.
    # Since we only have the API URL/Key, standard client DOES NOT support raw SQL execution for security.
    
    # Check if we can workaround or if we have to ask the user.
    # Actually, the user might have to run this manually in the dashboard.
    # BUT, we can try to create a function via the REST API? No, usually not.
    
    logging.warning("NOTICE: The Supabase Python Client cannot execute raw SQL directly without a helper function (RPC).")
    logging.warning("Please copy the content of 'add_vuln_columns.sql' and run it in your Supabase SQL Editor.")
    
    print("\n--- SQL TO RUN ---")
    print(sql_content)
    print("------------------\n")

if __name__ == "__main__":
    run_migration()
