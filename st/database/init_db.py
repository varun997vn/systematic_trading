"""
Database initialization script
Run this to create all tables
"""

from .database import Base, engine


def create_tables():
    """
    Create all database tables
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully!")
    print("\nTables created:")
    print("  - config (app settings & broker credentials)")
    print("  - strategies")
    print("  - trades")
    print("  - market_data")
    print("  - positions")


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    print("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped!")


def reset_database():
    """
    Reset database - drop and recreate all tables
    """
    print("Resetting database...")
    drop_tables()
    create_tables()
    print("✓ Database reset complete!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "create":
            create_tables()
        elif command == "drop":
            confirm = input("Are you sure you want to drop all tables? (yes/no): ")
            if confirm.lower() == "yes":
                drop_tables()
            else:
                print("Operation cancelled.")
        elif command == "reset":
            confirm = input("Are you sure you want to reset the database? (yes/no): ")
            if confirm.lower() == "yes":
                reset_database()
            else:
                print("Operation cancelled.")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: create, drop, reset")
    else:
        # Default: create tables if they don't exist
        create_tables()
