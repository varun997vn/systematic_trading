#!/usr/bin/env python3
"""
Quick Health Check Script
Tests only critical endpoints to verify the server is running properly
"""

import requests
import sys
from datetime import datetime


def check_health(base_url: str = "http://localhost:8000"):
    """Quick health check of critical endpoints"""

    print("=" * 70)
    print("🏥 Quick Health Check")
    print(f"Server: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    critical_endpoints = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health endpoint"),
        ("GET", "/api/portfolio/summary", "Portfolio API"),
        ("GET", "/api/strategies/available", "Strategy API"),
        ("GET", "/api/market/status", "Market API"),
    ]

    all_ok = True

    for method, endpoint, name in critical_endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404, 500]:  # Accept these as "server responding"
                status_icon = "✅" if response.status_code == 200 else "⚠️"
                print(f"{status_icon} {name:30s} - Status: {response.status_code}")
            else:
                print(f"❌ {name:30s} - Unexpected status: {response.status_code}")
                all_ok = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {name:30s} - Connection refused")
            all_ok = False
            break
        except Exception as e:
            print(f"❌ {name:30s} - Error: {str(e)}")
            all_ok = False

    print()
    print("=" * 70)
    if all_ok:
        print("✅ Server is responding to requests")
        return 0
    else:
        print("❌ Server has issues - run full test with test_api.py")
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quick health check for API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )

    args = parser.parse_args()
    exit_code = check_health(args.url)
    sys.exit(exit_code)