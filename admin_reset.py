#!/usr/bin/env python3

import sys
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Clear any existing admin users
        User.query.filter_by(role='admin').delete()
        db.session.commit()
        
        # Create a new admin user with a simple password
        admin = User()
        admin.username = 'admin'
        admin.email = 'admin@example.com'
        admin.set_password('admin123')
        admin.role = 'admin'
        admin.first_name = 'Admin'
        admin.last_name = 'User'
        
        # Save to database
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin created: {admin.username} / {admin.email}")
        print("Password: admin123")
        
if __name__ == "__main__":
    create_admin()