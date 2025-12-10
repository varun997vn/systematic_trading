#!/usr/bin/env python3
"""
CLI for Trading System API Server
Provides commands to run, manage, and configure the FastAPI server
"""

import sys
from pathlib import Path

import click
import uvicorn

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))


@click.group()
@click.version_option(version="1.0.0", prog_name="Trading System API")
def cli():
    """
    Trading System API - Command Line Interface

    Manage and run the FastAPI trading system server.
    """
    pass


@cli.command()
@click.option(
    '--host',
    default='0.0.0.0',
    help='Host to bind the server to',
    show_default=True
)
@click.option(
    '--port',
    default=8000,
    type=int,
    help='Port to bind the server to',
    show_default=True
)
@click.option(
    '--reload',
    is_flag=True,
    default=True,
    help='Enable auto-reload on code changes (development mode)'
)
@click.option(
    '--workers',
    default=1,
    type=int,
    help='Number of worker processes (production mode)',
    show_default=True
)
@click.option(
    '--log-level',
    default='info',
    type=click.Choice(['critical', 'error', 'warning', 'info', 'debug', 'trace']),
    help='Logging level',
    show_default=True
)
@click.option(
    '--access-log/--no-access-log',
    default=True,
    help='Enable/disable access logging',
    show_default=True
)
def run(host, port, reload, workers, log_level, access_log):
    """
    Run the FastAPI server

    Examples:

        Development mode with auto-reload:
        $ python cli.py run --reload

        Production mode with multiple workers:
        $ python cli.py run --workers 4 --no-reload

        Custom host and port:
        $ python cli.py run --host 127.0.0.1 --port 8080
    """
    click.echo("=" * 60)
    click.echo("Trading System API Server")
    click.echo("=" * 60)
    click.echo(f"Host: {host}")
    click.echo(f"Port: {port}")
    click.echo(f"Mode: {'Development (reload enabled)' if reload else 'Production'}")
    click.echo(f"Workers: {workers if not reload else 1}")
    click.echo(f"Log Level: {log_level}")
    click.echo("=" * 60)
    click.echo()
    click.echo("📊 API Documentation available at:")
    click.echo(f"   → http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    click.echo(f"   → http://{host if host != '0.0.0.0' else 'localhost'}:{port}/redoc")
    click.echo()
    click.echo("Press CTRL+C to quit")
    click.echo()

    try:
        # Import here to trigger database initialization
        from st.api.routes import app

        uvicorn.run(
            "st.api.routes:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level=log_level,
            access_log=access_log
        )
    except KeyboardInterrupt:
        click.echo("\n\n✓ Server stopped")
    except Exception as e:
        click.echo(f"\n❌ Error starting server: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--host',
    default='0.0.0.0',
    help='Host to bind the server to',
    show_default=True
)
@click.option(
    '--port',
    default=8000,
    type=int,
    help='Port to bind the server to',
    show_default=True
)
def dev(host, port):
    """
    Run the server in development mode (with auto-reload)

    Equivalent to: run --reload --log-level debug

    Example:
        $ python cli.py dev
    """
    click.echo("🚀 Starting development server...")
    click.echo()

    try:
        from st.api.routes import app

        uvicorn.run(
            "st.api.routes:app",
            host=host,
            port=port,
            reload=True,
            log_level="debug",
            access_log=True
        )
    except KeyboardInterrupt:
        click.echo("\n\n✓ Server stopped")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def check():
    """
    Check if the server configuration is valid

    Validates imports and database connection without starting the server.
    """
    click.echo("🔍 Checking server configuration...\n")

    errors = []

    # Check Python version
    if sys.version_info < (3, 9):
        errors.append("Python 3.9 or higher is required")
    else:
        click.echo("✓ Python version: {}.{}.{}".format(*sys.version_info[:3]))

    # Check if FastAPI is installed
    try:
        import fastapi
        click.echo(f"✓ FastAPI installed: {fastapi.__version__}")
    except ImportError:
        errors.append("FastAPI is not installed. Run: pip install fastapi")

    # Check if uvicorn is installed
    try:
        import uvicorn
        click.echo(f"✓ Uvicorn installed: {uvicorn.__version__}")
    except ImportError:
        errors.append("Uvicorn is not installed. Run: pip install uvicorn")

    # Check if app can be imported
    try:
        from st.api.routes import app
        click.echo("✓ App imports successfully")

        # Count routes
        route_count = len(app.routes)
        click.echo(f"✓ Found {route_count} routes")
    except ImportError as e:
        errors.append(f"Cannot import app: {e}")
    except Exception as e:
        errors.append(f"Error loading app: {e}")

    # Check data directory
    data_dir = Path("data")
    if data_dir.exists():
        click.echo(f"✓ Data directory exists: {data_dir.absolute()}")
    else:
        click.echo(f"⚠ Data directory not found: {data_dir.absolute()}")
        click.echo("  Creating data directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
        click.echo("  ✓ Created")

    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        click.echo(f"✓ Environment file exists: {env_file.absolute()}")
    else:
        click.echo(f"⚠ .env file not found")
        click.echo("  Consider creating one from .env.example")

    click.echo()

    if errors:
        click.echo("❌ Configuration check failed:\n")
        for error in errors:
            click.echo(f"  • {error}")
        sys.exit(1)
    else:
        click.echo("✅ All checks passed! Server is ready to run.")
        click.echo("\nTo start the server, run:")
        click.echo("  $ python cli.py run")


@cli.command()
def routes():
    """
    List all available API routes

    Shows all endpoints registered in the FastAPI application.
    """
    try:
        from st.api.routes import app

        click.echo("📋 Available API Routes:\n")

        routes_by_prefix = {}

        for route in app.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ', '.join(sorted(route.methods))
                path = route.path

                # Group by prefix
                prefix = path.split('/')[1] if len(path.split('/')) > 1 else 'root'
                if prefix not in routes_by_prefix:
                    routes_by_prefix[prefix] = []

                routes_by_prefix[prefix].append((methods, path, route.name))

        # Print grouped routes
        for prefix in sorted(routes_by_prefix.keys()):
            click.echo(f"\n{prefix.upper()}:")
            for methods, path, name in sorted(routes_by_prefix[prefix], key=lambda x: x[1]):
                click.echo(f"  {methods:20} {path:50} ({name})")

        total = sum(len(routes) for routes in routes_by_prefix.values())
        click.echo(f"\n📊 Total routes: {total}")

    except Exception as e:
        click.echo(f"❌ Error listing routes: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('ticker')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
def download(ticker, start_date, end_date):
    """
    Download market data for a ticker

    Example:
        $ python cli.py download AAPL --start-date 2023-01-01
    """
    click.echo(f"📥 Downloading data for {ticker}...")

    try:
        from st.data.data_manager import DataManager, DownloadRequest

        dm = DataManager()
        req = DownloadRequest(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            save=True
        )

        df = dm.download_stock_data(req)

        if df.empty:
            click.echo(f"❌ No data retrieved for {ticker}")
        else:
            click.echo(f"✓ Downloaded {len(df)} rows for {ticker}")
            click.echo(f"  Date range: {df.index[0]} to {df.index[-1]}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def init():
    """
    Initialize the trading system (database, directories, etc.)

    Creates necessary directories and initializes the database.
    """
    click.echo("🔧 Initializing trading system...\n")

    # Create data directory
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir(parents=True)
        click.echo(f"✓ Created data directory: {data_dir.absolute()}")
    else:
        click.echo(f"✓ Data directory exists: {data_dir.absolute()}")

    # Initialize database
    try:
        from st.database import init_db
        init_db()
        click.echo("✓ Database initialized")
    except Exception as e:
        click.echo(f"⚠ Database initialization: {e}")

    # Create .env if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        click.echo(f"✓ Created .env file from template")

    click.echo("\n✅ Initialization complete!")


@cli.command()
@click.option('--output', '-o', default='openapi.json', help='Output file path')
def export_openapi(output):
    """
    Export OpenAPI schema to a JSON file

    Example:
        $ python cli.py export-openapi --output api-schema.json
    """
    try:
        from st.api.routes import app
        import json

        schema = app.openapi()

        output_path = Path(output)
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=2)

        click.echo(f"✓ OpenAPI schema exported to: {output_path.absolute()}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--url', default='http://localhost:8000', help='API base URL')
def test(url):
    """
    Run basic API health checks

    Example:
        $ python cli.py test --url http://localhost:8000
    """
    import requests

    click.echo(f"🧪 Testing API at {url}...\n")

    tests = [
        ("Health Check", f"{url}/health"),
        ("Root Endpoint", f"{url}/"),
        ("API Docs", f"{url}/docs"),
    ]

    passed = 0
    failed = 0

    for name, endpoint in tests:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                click.echo(f"✓ {name}: OK")
                passed += 1
            else:
                click.echo(f"✗ {name}: Failed (Status: {response.status_code})")
                failed += 1
        except Exception as e:
            click.echo(f"✗ {name}: Error ({e})")
            failed += 1

    click.echo(f"\n📊 Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)


@cli.command()
def info():
    """
    Display system information and configuration
    """
    click.echo("📊 Trading System Information\n")

    click.echo(f"Python Version: {sys.version}")
    click.echo(f"Working Directory: {Path.cwd()}")

    try:
        from st.config.settings import Settings
        click.echo(f"\nData Directory: {Settings.DATA_DIR}")
        click.echo(f"Default Start Date: {Settings.DATA_START_DATE}")
        click.echo(f"Default End Date: {Settings.DATA_END_DATE}")
    except:
        pass

    # Check installed packages
    click.echo("\nInstalled Packages:")
    packages = ['fastapi', 'uvicorn', 'pandas', 'polars', 'yfinance', 'pydantic']
    for package in packages:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            click.echo(f"  • {package}: {version}")
        except ImportError:
            click.echo(f"  • {package}: not installed")


if __name__ == '__main__':
    cli()
