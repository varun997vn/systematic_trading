#!/usr/bin/env python3
"""
Quick script to check if your FastAPI backend is running
"""
import requests
import sys


def check_backend():
    ports = [8000, 8001, 5000, 3001]  # Common ports

    print("🔍 Checking for FastAPI backend...\n")

    for port in ports:
        url = f"http://localhost:{port}/health"
        try:
            print(f"Testing port {port}... ", end="")
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ FOUND! Backend is running on port {port}")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Port {port} responded but with status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ No service running")
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n❌ Backend not found on any common port!")
    print("\n📋 To start your FastAPI backend:")
    print("   1. Navigate to your backend directory")
    print("   2. Run: uvicorn main:app --reload --port 8000")
    print("   or: python main.py")
    return False


if __name__ == "__main__":
    if not check_backend():
        sys.exit(1)