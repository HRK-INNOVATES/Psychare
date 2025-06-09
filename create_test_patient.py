from app import app, db
from models import User, PatientInfo
from werkzeug.security import generate_password_hash
from datetime import date

def create_test_patient():
    with app.app_context():
        # Delete existing test patient if exists
        existing_user = User.query.filter_by(email='testpatient@example.com').first()
        if existing_user:
            if existing_user.patient_info:
                db.session.delete(existing_user.patient_info)
            db.session.delete(existing_user)
            db.session.commit()
        
        # Create new test patient
        user = User(
            username='testpatient',
            email='testpatient@example.com',
            role='patient',
            first_name='Test',
            last_name='Patient'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Create patient info
        patient_info = PatientInfo(
            user_id=user.id,
            dob=date(1990, 1, 1),
            gender='male',
            contact_number='123-456-7890'
        )
        db.session.add(patient_info)
        db.session.commit()
        
        print(f"Test patient created: {user.email} with password: testpass123")

if __name__ == '__main__':
    create_test_patient()