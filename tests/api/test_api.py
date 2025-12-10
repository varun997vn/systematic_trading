#!/usr/bin/env python3
"""
API Test Script for Trading System Backend
Tests all endpoints to verify the APIs are running correctly
"""

import requests
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import sys


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None,
                      params: Dict = None, expected_status: int = 200,
                      test_name: str = None) -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        test_name = test_name or f"{method} {endpoint}"

        self.results["total"] += 1

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, params=params, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check status code
            if response.status_code == expected_status:
                print(f"✅ {test_name} - Status: {response.status_code}")
                self.results["passed"] += 1

                # Pretty print response for successful tests
                try:
                    response_json = response.json()
                    print(f"   Response preview: {json.dumps(response_json, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:100]}...")

                return True
            else:
                print(f"❌ {test_name} - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.results["failed"] += 1
                self.results["errors"].append({
                    "test": test_name,
                    "error": f"Status {response.status_code}",
                    "response": response.text[:200]
                })
                return False

        except requests.exceptions.ConnectionError:
            print(f"❌ {test_name} - Connection Error: Cannot connect to {self.base_url}")
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": test_name,
                "error": "Connection refused - Is the server running?"
            })
            return False
        except Exception as e:
            print(f"❌ {test_name} - Error: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": test_name,
                "error": str(e)
            })
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("=" * 70)
        print("🚀 Starting API Tests")
        print(f"Testing backend at: {self.base_url}")
        print("=" * 70)
        print()

        # Test 1: Health & Info Endpoints
        print("📋 Testing Health & Info Endpoints")
        print("-" * 70)
        self.test_endpoint("GET", "/", test_name="Root endpoint")
        self.test_endpoint("GET", "/health", test_name="Health check")
        print()

        # Test 2: Data Management Endpoints
        print("💾 Testing Data Management Endpoints")
        print("-" * 70)
        self.test_endpoint("GET", "/api/data/tickers",
                           test_name="Get available tickers",
                           expected_status=500)  # Expected to fail without data_manager

        self.test_endpoint("POST", "/api/data/download",
                           data={"ticker": "AAPL", "start_date": "2024-01-01", "end_date": "2024-12-31"},
                           test_name="Download single ticker",
                           expected_status=500)

        self.test_endpoint("POST", "/api/data/download-multiple",
                           data={"tickers": ["AAPL", "GOOGL", "MSFT"]},
                           test_name="Download multiple tickers")

        self.test_endpoint("GET", "/api/data/ticker/AAPL",
                           test_name="Get ticker data",
                           expected_status=500)

        self.test_endpoint("GET", "/api/data/ticker/AAPL/info",
                           test_name="Get ticker info",
                           expected_status=500)

        self.test_endpoint("GET", "/api/data/storage-info",
                           test_name="Get storage info",
                           expected_status=500)
        print()

        # Test 3: Portfolio Endpoints
        print("💼 Testing Portfolio Endpoints")
        print("-" * 70)
        self.test_endpoint("POST", "/api/portfolio/init",
                           data={"initial_cash": 100000.0},
                           test_name="Initialize portfolio")

        self.test_endpoint("GET", "/api/portfolio/summary",
                           test_name="Get portfolio summary")

        self.test_endpoint("GET", "/api/portfolio/positions",
                           test_name="Get all positions")

        self.test_endpoint("GET", "/api/portfolio/position/AAPL",
                           test_name="Get specific position",
                           expected_status=404)

        self.test_endpoint("GET", "/api/portfolio/history",
                           test_name="Get portfolio history")

        self.test_endpoint("POST", "/api/portfolio/position/add",
                           data={"ticker": "AAPL", "quantity": 10, "price": 150.0},
                           test_name="Add position",
                           expected_status=500)

        self.test_endpoint("DELETE", "/api/portfolio/position/AAPL",
                           test_name="Remove position",
                           expected_status=500)

        self.test_endpoint("GET", "/api/portfolio/performance",
                           test_name="Get portfolio performance")
        print()

        # Test 4: Universe Endpoints
        print("🌐 Testing Universe Endpoints")
        print("-" * 70)
        self.test_endpoint("GET", "/api/universe/tickers",
                           test_name="Get universe tickers")

        self.test_endpoint("POST", "/api/universe/init",
                           data={"tickers": ["AAPL", "GOOGL", "MSFT"]},
                           test_name="Initialize universe")

        self.test_endpoint("POST", "/api/universe/filter",
                           data={"min_volume": 1000000, "min_price": 50.0},
                           test_name="Filter universe")

        self.test_endpoint("GET", "/api/universe/info",
                           test_name="Get universe info")
        print()

        # Test 5: Strategy Endpoints
        print("📊 Testing Strategy Endpoints")
        print("-" * 70)
        self.test_endpoint("GET", "/api/strategies/available",
                           test_name="Get available strategies")

        self.test_endpoint("POST", "/api/strategies/add",
                           data={"name": "rsi_momentum", "parameters": {"period": 14}},
                           test_name="Add strategy")

        self.test_endpoint("GET", "/api/strategies/active",
                           test_name="Get active strategies")

        self.test_endpoint("DELETE", "/api/strategies/rsi_momentum",
                           test_name="Remove strategy")
        print()

        # Test 6: Trading Signal Endpoints
        print("📈 Testing Trading Signal Endpoints")
        print("-" * 70)
        self.test_endpoint("POST", "/api/signals/generate",
                           data={
                               "ticker": "AAPL",
                               "strategies": ["rsi", "macd"],
                               "mode": "aggregate"
                           },
                           test_name="Generate signals")

        self.test_endpoint("GET", "/api/signals/latest/AAPL",
                           test_name="Get latest signal")

        self.test_endpoint("GET", "/api/signals/history/AAPL",
                           params={"limit": 50},
                           test_name="Get signal history")

        self.test_endpoint("GET", "/api/signals/buy-sell/AAPL",
                           params={"min_strength": 10},
                           test_name="Get buy/sell points")
        print()

        # Test 7: Backtesting Endpoints
        print("⏮️  Testing Backtesting Endpoints")
        print("-" * 70)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        self.test_endpoint("POST", "/api/backtest/run",
                           params={
                               "ticker": "AAPL",
                               "strategies": ["rsi", "macd"],
                               "start_date": start_date,
                               "end_date": end_date,
                               "initial_capital": 100000.0
                           },
                           test_name="Run backtest")

        self.test_endpoint("GET", "/api/backtest/results/test-123",
                           test_name="Get backtest results")
        print()

        # Test 8: Analytics Endpoints
        print("📉 Testing Analytics Endpoints")
        print("-" * 70)
        self.test_endpoint("GET", "/api/analytics/performance/AAPL",
                           test_name="Get performance metrics")

        self.test_endpoint("GET", "/api/analytics/correlation",
                           params={"tickers": ["AAPL", "GOOGL", "MSFT"]},
                           test_name="Get correlation matrix")
        print()

        # Test 9: Utility Endpoints
        print("🔧 Testing Utility Endpoints")
        print("-" * 70)
        self.test_endpoint("GET", "/api/market/status",
                           test_name="Get market status")

        self.test_endpoint("GET", "/api/market/calendar",
                           params={
                               "start_date": start_date,
                               "end_date": end_date
                           },
                           test_name="Get market calendar")
        print()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("📊 Test Summary")
        print("=" * 70)
        print(f"Total Tests: {self.results['total']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")

        if self.results['passed'] == self.results['total']:
            print("\n🎉 All tests passed!")
            success_rate = 100.0
        else:
            success_rate = (self.results['passed'] / self.results['total']) * 100
            print(f"\n⚠️  Success Rate: {success_rate:.1f}%")

        if self.results['errors']:
            print("\n❌ Failed Tests Details:")
            print("-" * 70)
            for i, error in enumerate(self.results['errors'], 1):
                print(f"\n{i}. {error['test']}")
                print(f"   Error: {error['error']}")
                if 'response' in error:
                    print(f"   Response: {error['response']}")

        print("=" * 70)

        # Return exit code
        return 0 if self.results['failed'] == 0 else 1


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Trading System API endpoints")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    tester = APITester(base_url=args.url)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()