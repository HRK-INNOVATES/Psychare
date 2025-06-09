#!/usr/bin/env python3
"""
Update doctor profile photos with appropriate SVG avatars
"""

from app import app, db
from models import User, DoctorInfo

def update_doctor_photos():
    """Update all doctors with appropriate profile photos"""
    
    with app.app_context():
        # Get all doctors
        doctors = db.session.query(User).join(DoctorInfo).filter(User.role == 'doctor').all()
        
        # Photo assignments based on doctor specialization and name
        photo_mapping = {
            'Clinical Psychology': '/static/images/doctors/dr-placeholder-female-1.svg',
            'Cognitive Behavioral Therapy': '/static/images/doctors/dr-placeholder-male-1.svg',
            'Family Therapy': '/static/images/doctors/dr-placeholder-female-2.svg',
            'Child Psychology': '/static/images/doctors/dr-placeholder-female-1.svg',
            'Addiction Counseling': '/static/images/doctors/dr-placeholder-male-2.svg',
            'Marriage Counseling': '/static/images/doctors/dr-placeholder-female-2.svg',
            'Trauma Therapy': '/static/images/doctors/dr-placeholder-male-1.svg',
            'Depression Treatment': '/static/images/doctors/dr-placeholder-female-1.svg',
            'Anxiety Disorders': '/static/images/doctors/dr-placeholder-male-2.svg',
            'PTSD Treatment': '/static/images/doctors/dr-placeholder-male-1.svg'
        }
        
        # Alternative assignment by doctor name/gender patterns
        female_names = ['sarah', 'emily', 'jessica', 'maria', 'lisa', 'jennifer', 'amanda', 'rachel']
        male_names = ['michael', 'david', 'james', 'robert', 'john', 'william', 'thomas', 'richard']
        
        for doctor in doctors:
            if doctor.doctor_info:
                # First try to assign based on specialization
                if doctor.doctor_info.specialization in photo_mapping:
                    photo_url = photo_mapping[doctor.doctor_info.specialization]
                else:
                    # Assign based on name pattern
                    first_name = doctor.first_name.lower() if doctor.first_name else ''
                    
                    if any(name in first_name for name in female_names):
                        # Alternate between female avatars
                        photo_url = '/static/images/doctors/dr-placeholder-female-1.svg' if doctor.id % 2 == 0 else '/static/images/doctors/dr-placeholder-female-2.svg'
                    elif any(name in first_name for name in male_names):
                        # Alternate between male avatars
                        photo_url = '/static/images/doctors/dr-placeholder-male-1.svg' if doctor.id % 2 == 0 else '/static/images/doctors/dr-placeholder-male-2.svg'
                    else:
                        # Default assignment based on ID
                        if doctor.id % 4 == 0:
                            photo_url = '/static/images/doctors/dr-placeholder-female-1.svg'
                        elif doctor.id % 4 == 1:
                            photo_url = '/static/images/doctors/dr-placeholder-male-1.svg'
                        elif doctor.id % 4 == 2:
                            photo_url = '/static/images/doctors/dr-placeholder-female-2.svg'
                        else:
                            photo_url = '/static/images/doctors/dr-placeholder-male-2.svg'
                
                # Update the doctor's profile photo
                doctor.doctor_info.profile_photo = photo_url
                print(f"Updated Dr. {doctor.get_full_name()} ({doctor.doctor_info.specialization}) with {photo_url}")
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully updated profile photos for {len(doctors)} doctors")

if __name__ == '__main__':
    update_doctor_photos()