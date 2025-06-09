from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, DoctorInfo, PatientInfo, Availability, Appointment, SliderImage

def seed_database():
    # Clear existing data
    print("Clearing existing data...")
    db.session.query(Appointment).delete()
    db.session.query(Availability).delete()
    db.session.query(DoctorInfo).delete()
    db.session.query(PatientInfo).delete()
    db.session.query(SliderImage).delete()
    db.session.query(User).delete()
    db.session.commit()
    
    print("Creating admin user...")
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        first_name='Admin',
        last_name='User',
        is_active=True
    )
    db.session.add(admin)
    db.session.commit()
    
    print("Creating doctors...")
    # Create doctors
    doctor_data = [
        {
            'username': 'dr_smith',
            'email': 'smith@example.com',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Smith',
            'specialization': 'Clinical Psychology',
            'qualification': 'Ph.D. Clinical Psychology',
            'experience_years': 10,
            'bio': 'Dr. Smith specializes in treating depression and anxiety disorders.',
            'is_approved': True
        },
        {
            'username': 'dr_jones',
            'email': 'jones@example.com',
            'password': 'password123',
            'first_name': 'Emily',
            'last_name': 'Jones',
            'specialization': 'Child Psychology',
            'qualification': 'Ph.D. Child Psychology',
            'experience_years': 8,
            'bio': 'Dr. Jones works with children dealing with developmental issues.',
            'is_approved': True
        },
        {
            'username': 'dr_wilson',
            'email': 'wilson@example.com',
            'password': 'password123',
            'first_name': 'David',
            'last_name': 'Wilson',
            'specialization': 'Cognitive Behavioral Therapy',
            'qualification': 'M.D. Psychiatry',
            'experience_years': 15,
            'bio': 'Dr. Wilson specializes in cognitive behavioral therapy for various mental health issues.',
            'is_approved': True
        }
    ]
    
    doctors = []
    for data in doctor_data:
        doctor = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='doctor',
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_active=True
        )
        db.session.add(doctor)
        db.session.flush()  # To get doctor.id
        
        doctor_info = DoctorInfo(
            user_id=doctor.id,
            specialization=data['specialization'],
            qualification=data['qualification'],
            experience_years=data['experience_years'],
            bio=data['bio'],
            is_approved=data['is_approved']
        )
        db.session.add(doctor_info)
        doctors.append((doctor, doctor_info))
    
    db.session.commit()
    
    print("Creating availabilities for doctors...")
    # Create availabilities for doctors
    for _, doctor_info in doctors:
        # Monday, Wednesday, Friday morning
        for day in [0, 2, 4]:  # Monday=0, Wednesday=2, Friday=4
            availability = Availability(
                doctor_id=doctor_info.id,
                day_of_week=day,
                start_time=time(9, 0),  # 9:00 AM
                end_time=time(12, 0),   # 12:00 PM
                is_active=True
            )
            db.session.add(availability)
        
        # Tuesday, Thursday afternoon
        for day in [1, 3]:  # Tuesday=1, Thursday=3
            availability = Availability(
                doctor_id=doctor_info.id,
                day_of_week=day,
                start_time=time(13, 0),  # 1:00 PM
                end_time=time(17, 0),    # 5:00 PM
                is_active=True
            )
            db.session.add(availability)
    
    db.session.commit()
    
    print("Creating patients...")
    # Create patients
    patient_data = [
        {
            'username': 'patient1',
            'email': 'patient1@example.com',
            'password': 'password123',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'dob': date(1990, 5, 15),
            'gender': 'female',
            'contact_number': '555-123-4567'
        },
        {
            'username': 'patient2',
            'email': 'patient2@example.com',
            'password': 'password123',
            'first_name': 'Bob',
            'last_name': 'Williams',
            'dob': date(1985, 8, 22),
            'gender': 'male',
            'contact_number': '555-987-6543'
        }
    ]
    
    patients = []
    for data in patient_data:
        patient = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='patient',
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_active=True
        )
        db.session.add(patient)
        db.session.flush()  # To get patient.id
        
        patient_info = PatientInfo(
            user_id=patient.id,
            dob=data['dob'],
            gender=data['gender'],
            contact_number=data['contact_number']
        )
        db.session.add(patient_info)
        patients.append((patient, patient_info))
    
    db.session.commit()
    
    print("Creating appointments...")
    # Create sample appointments
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    # Appointment 1: Patient 1 with Doctor 1 (tomorrow)
    appointment1 = Appointment(
        doctor_id=doctors[0][1].id,
        patient_id=patients[0][1].id,
        appointment_date=tomorrow,
        start_time=time(10, 0),  # 10:00 AM
        end_time=time(11, 0),    # 11:00 AM
        status='confirmed',
        notes='Initial consultation'
    )
    db.session.add(appointment1)
    
    # Appointment 2: Patient 2 with Doctor 2 (next week)
    appointment2 = Appointment(
        doctor_id=doctors[1][1].id,
        patient_id=patients[1][1].id,
        appointment_date=next_week,
        start_time=time(14, 0),  # 2:00 PM
        end_time=time(15, 0),    # 3:00 PM
        status='pending',
        notes='Follow-up session'
    )
    db.session.add(appointment2)
    
    # Appointment 3: Patient 1 with Doctor 3 (next week)
    appointment3 = Appointment(
        doctor_id=doctors[2][1].id,
        patient_id=patients[0][1].id,
        appointment_date=next_week + timedelta(days=1),
        start_time=time(15, 0),  # 3:00 PM
        end_time=time(16, 0),    # 4:00 PM
        status='pending',
        notes='Consultation for specific issues'
    )
    db.session.add(appointment3)
    
    db.session.commit()
    
    print("Creating slider images...")
    # Create slider images
    slider_data = [
        {
            'title': 'Professional Psychological Counseling',
            'description': 'Get professional help from certified psychologists',
            'image_url': 'https://images.pexels.com/photos/5699456/pexels-photo-5699456.jpeg',
            'display_order': 1,
            'is_active': True
        },
        {
            'title': 'Online Therapy Sessions',
            'description': 'Convenient video consultations from the comfort of your home',
            'image_url': 'https://images.pexels.com/photos/7176319/pexels-photo-7176319.jpeg',
            'display_order': 2,
            'is_active': True
        },
        {
            'title': 'Specialized Mental Health Services',
            'description': 'Expert care for a wide range of psychological conditions',
            'image_url': 'https://images.pexels.com/photos/6124375/pexels-photo-6124375.jpeg',
            'display_order': 3,
            'is_active': True
        }
    ]
    
    for data in slider_data:
        slider = SliderImage(
            title=data['title'],
            description=data['description'],
            image_url=data['image_url'],
            display_order=data['display_order'],
            is_active=data['is_active']
        )
        db.session.add(slider)
    
    db.session.commit()
    
    print("Database seeded successfully!")

if __name__ == "__main__":
    with app.app_context():
        seed_database()