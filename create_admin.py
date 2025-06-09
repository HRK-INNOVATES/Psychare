from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user(username, email, password):
    """Create an admin user"""
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username} ({existing_admin.email})")
            return existing_admin
        
        # Create new admin user
        admin = User()
        admin.username = username
        admin.email = email
        admin.password_hash = generate_password_hash(password)
        admin.role = 'admin'
        admin.first_name = 'Admin'
        admin.last_name = 'User'
        admin.is_active = True
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user created successfully: {username} ({email})")
        return admin

if __name__ == "__main__":
    # Create admin user with these credentials
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = "admin123"
    
    create_admin_user(admin_username, admin_email, admin_password)