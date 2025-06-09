from app import app, db
from models import User, DoctorInfo
from werkzeug.security import generate_password_hash
import random
from datetime import datetime

def seed_doctors():
    """
    Add doctors to the database
    """
    # Doctor data from the provided table
    doctors_data = [
        {"name": "Dr. Amarpreet", "rating": 4.9, "area": "Kamla Nagar", "years": 13, "contact": "08401732925"},
        {"name": "Dr. Apoorv Yadav - Mind Palace", "rating": 4.8, "area": "Delhi Gate", "years": 8, "contact": "08460249428"},
        {"name": "Aadhar Brain Creativity Centre", "rating": 5.0, "area": "Sikandra", "years": 10, "contact": ""},
        {"name": "Dr. Sarang Dhar", "rating": 4.7, "area": "Gandhi Nagar", "years": 24, "contact": "08511494425"},
        {"name": "Dr. Pallavee Walia (Blossom Clinic)", "rating": 4.6, "area": "Dayal Bagh", "years": 9, "contact": ""},
        {"name": "Mind Healing Centre", "rating": 5.0, "area": "Shastripuram", "years": 1, "contact": ""},
        {"name": "Dr. Chinu Agrawal", "rating": 4.9, "area": "Sikandra", "years": 25, "contact": ""},
        {"name": "Mind Care Neuro Psychiatric Clinic", "rating": 4.9, "area": "Yamuna Colony", "years": 6, "contact": ""},
        {"name": "Mann Clinic (Dr. Mohit Jain)", "rating": 4.8, "area": "Taj Nagari", "years": 3, "contact": ""},
        {"name": "Baghel Brain & Headache Clinic", "rating": 4.9, "area": "Shaheed Nagar", "years": None, "contact": ""},
        {"name": "Dr. Prabhat Sharma Clinic", "rating": 4.9, "area": "Hari Parbat", "years": 13, "contact": ""},
        {"name": "The 5 Lotus Clinic", "rating": 4.9, "area": "Avas Vikas", "years": 9, "contact": ""},
        {"name": "Emotion of Life", "rating": 4.6, "area": "Kamla Nagar", "years": None, "contact": ""}
    ]

    specializations = [
        "Clinical Psychology", 
        "Counseling Psychology", 
        "Neuropsychology", 
        "Health Psychology", 
        "Child Psychology",
        "Educational Psychology",
        "Cognitive Behavioral Therapy",
        "Psychoanalysis"
    ]

    qualifications = [
        "Ph.D. in Psychology",
        "M.Phil in Clinical Psychology",
        "Master's in Counseling Psychology",
        "Doctorate in Neuropsychology",
        "M.D. in Psychiatry",
        "M.S. in Clinical Mental Health",
        "Licensed Professional Counselor"
    ]

    with app.app_context():
        # Check if doctors already exist to avoid duplicates
        if User.query.filter(User.role == 'doctor').count() >= len(doctors_data):
            print("Doctors already exist in the database.")
            return
        
        for doctor in doctors_data:
            # Extract name parts
            full_name = doctor["name"].split(" - ")[0]  # Remove clinic name if present
            if "(" in full_name:
                full_name = full_name.split("(")[0].strip()  # Remove clinic name in parentheses
                
            name_parts = full_name.split()
            
            # Handle cases where it's a clinic rather than a doctor
            if name_parts[0] != "Dr.":
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            else:
                first_name = name_parts[1]
                last_name = " ".join(name_parts[2:]) if len(name_parts) > 2 else ""
            
            # Create username from name (lowercase with underscores)
            username = f"{first_name.lower()}_{last_name.lower()}".replace(" ", "_")
            if not username:
                # Use clinic name if no personal name available
                username = doctor["name"].replace(" ", "_").lower()
            
            # Create email from username
            email = f"{username}@example.com"
            
            # Create a random but strong password
            password = generate_password_hash("Doctor123!")
            
            # Create the user record
            user = User(
                username=username,
                email=email,
                password_hash=password,
                role='doctor',
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.flush()  # Generate ID for the new user
            
            # Create doctor info
            doctor_info = DoctorInfo(
                user_id=user.id,
                specialization=random.choice(specializations),
                qualification=random.choice(qualifications),
                experience_years=doctor["years"] if doctor["years"] else random.randint(1, 15),
                bio=f"Practicing in {doctor['area']} with a rating of {doctor['rating']}. Contact: {doctor['contact'] if doctor['contact'] else 'Not available'}",
                is_approved=True  # Auto-approve these doctors
            )
            
            db.session.add(doctor_info)
        
        # Commit all changes to the database
        db.session.commit()
        print(f"Added {len(doctors_data)} doctors to the database.")

if __name__ == "__main__":
    seed_doctors()