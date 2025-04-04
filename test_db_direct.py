# test_db_direct.py
import pg8000
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Get database URL
db_url = os.environ.get('DATABASE_URL')

# Parse database URL
parsed = urlparse(db_url)
dbname = parsed.path[1:]  # Remove leading '/'
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port or 5432

print(f"Connecting to {host}:{port}/{dbname} as {user}")

# Connect directly without any SSL parameters
conn = pg8000.connect(
    user=user,
    password=password,
    host=host,
    port=port,
    database=dbname
)

# Test query
cursor = conn.cursor()
cursor.execute("SELECT version();")
version = cursor.fetchone()[0]
print(f"Connected successfully: {version}")

# Close connection
conn.close()