#!/usr/bin/env python
"""
Database management script for Planventure API
Usage:
    python manage.py create_db  - Create all database tables
    python manage.py drop_db    - Drop all database tables
    python manage.py reset_db   - Drop and recreate all tables
"""
import sys
from app import create_app
from extensions import db


def create_db():
    """Create all database tables."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully!")


def drop_db():
    """Drop all database tables."""
    app = create_app()
    with app.app_context():
        db.drop_all()
        print("✓ Database tables dropped successfully!")


def reset_db():
    """Drop and recreate all database tables."""
    app = create_app()
    with app.app_context():
        db.drop_all()
        print("✓ Dropped existing tables")
        db.create_all()
        print("✓ Created new tables")
        print("✓ Database reset complete!")


if __name__ == '__main__':
    commands = {
        'create_db': create_db,
        'drop_db': drop_db,
        'reset_db': reset_db,
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: python manage.py [command]")
        print("\nAvailable commands:")
        print("  create_db  - Create all database tables")
        print("  drop_db    - Drop all database tables")
        print("  reset_db   - Drop and recreate all tables")
        sys.exit(1)
    
    command = sys.argv[1]
    commands[command]()
