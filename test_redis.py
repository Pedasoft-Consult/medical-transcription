"""
Test script to verify Redis connectivity
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_redis_directly():
    """Test Redis connection directly without using utility functions"""
    try:
        import redis

        # Get Redis URL from environment
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            print("❌ REDIS_URL environment variable not set")
            return {
                "status": "error",
                "message": "REDIS_URL environment variable not set"
            }

        # Hide password in URL for logging
        safe_url = redis_url
        if '@' in redis_url:
            parts = redis_url.split('@')
            safe_url = f"redis://*****@{parts[1]}" if len(parts) > 1 else redis_url

        print(f"🔗 Connecting to Redis at {safe_url}")

        # Try to connect with more detailed error handling
        try:
            # Create Redis client
            client = redis.from_url(
                url=redis_url,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )

            # Test ping
            ping_result = client.ping()
            print(f"✅ Redis PING result: {ping_result}")

            # Test basic operations
            test_key = "test_redis_connection"
            test_value = "test_value_" + os.urandom(4).hex()

            # Set value
            set_result = client.set(test_key, test_value)
            print(f"✅ Redis SET result: {set_result}")

            # Get value
            get_result = client.get(test_key)
            print(f"✅ Redis GET result: {get_result}")

            # Delete key
            del_result = client.delete(test_key)
            print(f"✅ Redis DEL result: {del_result}")

            # Get server info
            info = client.info()

            return {
                "status": "connected",
                "message": "Redis connection successful",
                "details": {
                    "redis_version": info.get('redis_version'),
                    "uptime_days": info.get('uptime_in_days'),
                    "connected_clients": info.get('connected_clients'),
                    "used_memory_human": info.get('used_memory_human')
                }
            }
        except redis.exceptions.ConnectionError as e:
            print(f"❌ Redis connection error: {str(e)}")
            return {
                "status": "error",
                "message": f"Connection error: {str(e)}",
                "error_type": "connection_error"
            }
        except redis.exceptions.TimeoutError as e:
            print(f"❌ Redis timeout error: {str(e)}")
            return {
                "status": "error",
                "message": f"Timeout error: {str(e)}",
                "error_type": "timeout_error"
            }
        except redis.exceptions.AuthenticationError as e:
            print(f"❌ Redis authentication error: {str(e)}")
            return {
                "status": "error",
                "message": f"Authentication error: {str(e)}",
                "error_type": "auth_error"
            }
        except Exception as e:
            print(f"❌ Unexpected Redis error: {str(e)}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error"
            }
    except ImportError:
        print("❌ Redis module not installed")
        return {
            "status": "error",
            "message": "Redis module not installed. Try: pip install redis",
            "error_type": "import_error"
        }


def main():
    """Run Redis connection test and print diagnostics"""
    print("🔍 Testing Redis connection...")

    # Test using direct Redis connection first
    direct_results = test_redis_directly()

    # If direct test succeeds, we're good
    if direct_results["status"] == "connected":
        print("\n=== Redis Connection Direct Test Results ===")
        print(f"Status: \033[92mconnected\033[0m")  # Green for connected
        print(f"Message: {direct_results['message']}")

        # Print details if available
        if "details" in direct_results and direct_results["details"]:
            print("\nRedis Server Information:")
            for key, value in direct_results["details"].items():
                print(f"  - {key}: {value}")

        print("\n✅ Redis connection is working properly. No action needed.")
        return 0

    # Otherwise, try the utility function as fallback
    try:
        from api.utils.redis_fix import test_redis_connection
        results = test_redis_connection()

        print("\n=== Redis Connection Test Results ===")

        # Print status with color
        status = results.get("status", "unknown")
        if status == "connected":
            print(f"Status: \033[92m{status}\033[0m")  # Green for connected
        elif status == "error":
            print(f"Status: \033[91m{status}\033[0m")  # Red for error
        else:
            print(f"Status: \033[93m{status}\033[0m")  # Yellow for unknown

        # Print message
        if "message" in results:
            print(f"Message: {results['message']}")

        # Print URL (with password hidden)
        if "url" in results:
            print(f"Redis URL: {results['url']}")

        # Print details if available
        if "details" in results and results["details"]:
            print("\nRedis Server Information:")
            for key, value in results["details"].items():
                print(f"  - {key}: {value}")

        # Print operations test result if available
        if "operations_test" in results:
            test_result = results["operations_test"]
            if test_result == "passed":
                print(f"\nOperations Test: \033[92mPASSED\033[0m")  # Green for passed
            else:
                print(f"\nOperations Test: \033[91mFAILED\033[0m")  # Red for failed

        # Print any error information
        if "error_type" in results:
            print(f"\nError Type: {results['error_type']}")

        print("\n=== Troubleshooting Tips ===")
        if status == "connected":
            print("✅ Redis connection is working properly. No action needed.")
        else:
            print("1. Verify the REDIS_URL in your .env file is correct")
            print("2. Check if the Redis server is running and accessible")
            print("3. Ensure firewall settings allow connections to the Redis port")
            print("4. If using Redis Cloud or other service, verify your credentials are valid")
            print("5. For connection refused errors, check if Redis is running on the specified host/port")
            print("6. Try manually testing the connection with the redis-cli tool")
            print("7. Check TLS/SSL requirements for your Redis instance")

        # Return a success/failure exit code
        return 0 if status == "connected" else 1

    except Exception as e:
        print(f"\n❌ Error testing Redis connection: {str(e)}")
        print("\n=== Troubleshooting Tips ===")
        print("1. Check if the api/utils/redis_fix.py module exists and is accessible")
        print("2. Verify that all required packages are installed (pip install -r requirements.txt)")
        print("3. Try installing redis directly: pip install redis")

        return 1


if __name__ == "__main__":
    sys.exit(main())