"""
Test PostgreSQL connection with pg8000
"""
import os
import sys
import time
import ssl
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

        try:
            # Create SSL context for secure connections
            ssl_context = ssl.create_default_context()
            # Don't verify server certificate for testing
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            print("Attempting connection with SSL context...")
            # Connect with pg8000 using ssl_context
            conn = pg8000.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=dbname,
                ssl_context=ssl_context
            )
            ssl_type = "ssl_context"
        except Exception as e:
            print(f"SSL context connection failed: {e}")
            print("Trying with ssl=True parameter...")
            # Fall back to ssl=True if ssl_context fails
            conn = pg8000.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=dbname,
                ssl=True
            )
            ssl_type = "ssl=True"

        # Connection successful
        print(f"✅ Connected to PostgreSQL database in {time.time() - start_time:.2f} seconds using {ssl_type}")

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
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                    row_count = cursor.fetchone()[0]
                    print(f"  - {table[0]}: {row_count} rows")
                except Exception as e:
                    print(f"  - {table[0]}: Error counting rows: {e}")
        else:
            print("⚠️ No tables found in the 'public' schema")

        # Test create a temporary table
        print("\n📊 Testing write permissions...")
        try:
            # Create a temp table
            cursor.execute("""
            CREATE TEMPORARY TABLE test_connection (
                id SERIAL PRIMARY KEY,
                test_value VARCHAR(50)
            );
            """)

            # Insert a row
            cursor.execute("INSERT INTO test_connection (test_value) VALUES ('test');")

            # Query to verify
            cursor.execute("SELECT * FROM test_connection;")
            test_data = cursor.fetchall()
            print(f"✅ Write test successful: {test_data}")

            # Clean up
            cursor.execute("DROP TABLE test_connection;")
            conn.commit()
        except Exception as e:
            print(f"❌ Write test failed: {str(e)}")
            # Try to rollback if possible
            try:
                conn.rollback()
            except:
                pass

        # Close connection
        conn.close()
        print("\n✅ Database connection test completed successfully!")
        return True

    except ImportError:
        print("❌ pg8000 module not found. Please install it with: pip install pg8000")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")

        # Try SQLAlchemy connection as a fallback
        try:
            print("\n📊 Trying SQLAlchemy connection as fallback...")
            from sqlalchemy import create_engine, text

            # Convert postgres:// to postgresql+pg8000://
            if db_url.startswith('postgres://'):
                engine_url = db_url.replace('postgres://', 'postgresql+pg8000://')
            elif db_url.startswith('postgresql://'):
                engine_url = db_url.replace('postgresql://', 'postgresql+pg8000://')
            else:
                engine_url = db_url

            # Create engine with SSL options
            engine = create_engine(
                engine_url,
                connect_args={
                    "ssl_context": ssl.create_default_context()
                }
            )

            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                data = result.fetchone()
                print(f"✅ SQLAlchemy connection successful: {data}")
                return True
        except Exception as e2:
            print(f"❌ SQLAlchemy connection also failed: {str(e2)}")

        return False


if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)