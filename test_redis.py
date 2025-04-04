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

# Import Redis utility
from api.utils.redis_fix import test_redis_connection


def main():
    """Run Redis connection test and print diagnostics"""
    print("🔍 Testing Redis connection...")
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

    # Return a success/failure exit code
    return 0 if status == "connected" else 1


if __name__ == "__main__":
    sys.exit(main())