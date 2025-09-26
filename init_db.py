#!/usr/bin/env python3
"""
Database initialization script for the affiliate deal aggregator.
Run this script to create all database tables.
"""

from app import app
from models import db, Deal, Admin, Newsletter
import os

def init_database():
    """Initialize the database with all tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = Admin.query.first()
        if not admin:
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin = Admin(username='admin')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Created admin user with password: {admin_password}")
        else:
            print("Admin user already exists")
        
        print("Database initialized successfully!")
        print("Tables created:")
        print("- deals")
        print("- admin")
        print("- newsletter")

if __name__ == '__main__':
    init_database()