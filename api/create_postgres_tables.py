# app/create_postgres_tables.py
import os
import sys
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Support DATABASE_URL or broken-out env vars
def get_pg_config():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print("Using DATABASE_URL:", db_url)
        result = urlparse(db_url)
        return {
            "dbname": result.path[1:],
            "user": result.username,
            "password": result.password,
            "host": result.hostname,
            "port": result.port or "5432"
        }
    else:
        print("Using individual POSTGRES_* environment variables")
        return {
            "dbname": os.getenv("POSTGRES_DATABASE"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
            "host": os.getenv("POSTGRES_HOST"),
            "port": os.getenv("POSTGRES_PORT", "5432")
        }

def connect_postgres():
    """Connect to PostgreSQL database"""
    config = get_pg_config()
    try:
        conn = psycopg2.connect(**config)
        print(f"✅ Connected to PostgreSQL database: {config['dbname']}")
        return conn
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL connection error: {e}")
        sys.exit(1)

def create_tables(conn):
    """Create tables in PostgreSQL"""
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE,
        email VARCHAR(255) UNIQUE,
        hashed_password VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcriptions (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255),
        content TEXT,
        user_id INTEGER REFERENCES users(id),
        file_path VARCHAR(255),
        language VARCHAR(10) DEFAULT 'en',
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS translations (
        id SERIAL PRIMARY KEY,
        transcription_id INTEGER REFERENCES transcriptions(id),
        content TEXT,
        source_language VARCHAR(10),
        target_language VARCHAR(10),
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)

    conn.commit()
    print("✅ Tables created successfully!")

def main():
    pg_conn = connect_postgres()
    create_tables(pg_conn)
    pg_conn.close()

if __name__ == "__main__":
    main()