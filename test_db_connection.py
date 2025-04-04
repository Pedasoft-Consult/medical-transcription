"""
Test PostgreSQL connection with pg8000
"""
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_postgres_connection():
    """Test the PostgreSQL connection"""
    print("\n🔍 Testing PostgreSQL Connection...\n")

    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL environment variable not set")
        return False

    # Print database URL (hiding credentials)
    masked_url = db_url
    if '@' in db_url:
        parts = db_url.split('@')
        credentials = parts[0].split(':')
        if len(credentials) > 2:
            credentials[2] = '***'  # Mask password
        parts[0] = ':'.join(credentials)
        masked_url = '@'.join(parts)

    print(f"📌 Using database URL: {masked_url}")

    # Parse database URL to extract connection parameters
    try:
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(db_url)
        dbname = parsed.path[1:]  # Remove leading '/'
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432

        # Extract SSL mode from query parameters
        query = urlparse.parse_qs(parsed.query)
        ssl_mode = query.get('sslmode', ['prefer'])[0]

        print(f"🔹 Host: {host}")
        print(f"🔹 Port: {port}")
        print(f"🔹 Database: {dbname}")
        print(f"🔹 User: {user}")
        print(f"🔹 SSL Mode: {ssl_mode}")
    except Exception as e:
        print(f"❌ Error parsing database URL: {str(e)}")
        return False

    # Try to connect using pg8000
    try:
        import pg8000

        print("\n📊 Connecting with pg8000...")
        start_time = time.time()

        # Connect with pg8000
        conn = pg8000.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
            ssl=True  # For pg8000, use ssl=True instead of sslmode
        )

        # Connection successful
        print(f"✅ Connected to PostgreSQL database in {time.time() - start_time:.2f} seconds")

        # Execute a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        print(f"📌 PostgreSQL Version: {version}")

        # Check tables
        print("\n📊 Checking database tables...")
        cursor.execute("""
            SELECT tablename FROM pg_catalog.pg_tables
            WHERE schemaname='public';
        """)

        tables = cursor.fetchall()
        if tables:
            print("📌 Available tables:")
            for table in tables:
                # Count rows in each table
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                row_count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {row_count} rows")
        else:
            print("⚠️ No tables found in the 'public' schema")

        # Close connection
        conn.close()
        print("\n✅ Database connection test completed successfully!")
        return True

    except ImportError:
        print("❌ pg8000 module not found. Please install it with: pip install pg8000")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)