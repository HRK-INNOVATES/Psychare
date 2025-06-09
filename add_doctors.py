from app import app, db
from models import User, DoctorInfo
from werkzeug.security import generate_password_hash
import random
from datetime import datetime
import string

# Doctor data from the provided table
doctors_data = [
    {"name": "Dr. Amarpreet", "rating": 4.9, "area": "Kamla Nagar", "years": 13, "contact": "08401732925"},
    {"name": "Dr. Apoorv Yadav", "clinic": "Mind Palace", "rating": 4.8, "area": "Delhi Gate", "years": 8, "contact": "08460249428"},
    {"name": "Aadhar Brain Creativity Centre", "rating": 5.0, "area": "Sikandra", "years": 10, "contact": ""},
    {"name": "Dr. Sarang Dhar", "rating": 4.7, "area": "Gandhi Nagar", "years": 24, "contact": "08511494425"},
    {"name": "Dr. Pallavee Walia", "clinic": "Blossom Clinic", "rating": 4.6, "area": "Dayal Bagh", "years": 9, "contact": ""},
    {"name": "Mind Healing Centre", "rating": 5.0, "area": "Shastripuram", "years": 1, "contact": ""},
    {"name": "Dr. Chinu Agrawal", "rating": 4.9, "area": "Sikandra", "years": 25, "contact": ""},
    {"name": "Mind Care Neuro Psychiatric Clinic", "rating": 4.9, "area": "Yamuna Colony", "years": 6, "contact": ""},
    {"name": "Dr. Mohit Jain", "clinic": "Mann Clinic", "rating": 4.8, "area": "Taj Nagari", "years": 3, "contact": ""},
    {"name": "Baghel Brain & Headache Clinic", "rating": 4.9, "area": "Shaheed Nagar", "years": 5, "contact": ""},
    {"name": "Dr. Prabhat Sharma", "clinic": "Clinic", "rating": 4.9, "area": "Hari Parbat", "years": 13, "contact": ""},
    {"name": "The 5 Lotus Clinic", "rating": 4.9, "area": "Avas Vikas", "years": 9, "contact": ""},
    {"name": "Emotion of Life", "rating": 4.6, "area": "Kamla Nagar", "years": 3, "contact": ""}
]

specializations = [
    "Clinical Psychology", 
    "Counseling Psychology", 
    "Neuropsychology", 
    "Health Psychology", 
    "Child Psychology"
]

qualifications = [
    "Ph.D. in Psychology",
    "M.Phil in Clinical Psychology",
    "Master's in Counseling Psychology",
    "M.D. in Psychiatry"
]

def generate_username(name):
    """Generate a username from a name"""
    # Clean the name and convert to lowercase
    name = ''.join(c for c in name if c.isalnum() or c.isspace()).lower()
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Add random string to ensure uniqueness
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{name}_{random_suffix}"

def add_doctors():
    try:
        with app.app_context():
            # Process each doctor
            for doctor_data in doctors_data:
                # Get or create a username
                name = doctor_data["name"]
                
                # Extract first and last name
                if name.startswith("Dr."):
                    parts = name.split(" ", 2)
                    first_name = parts[1]
                    last_name = parts[2] if len(parts) > 2 else ""
                elif "Centre" in name or "Clinic" in name:
                    # For clinics, use a generic doctor name
                    first_name = "Doctor"
                    last_name = "at " + name
                else:
                    parts = name.split(" ", 1)
                    first_name = parts[0]
                    last_name = parts[1] if len(parts) > 1 else ""
                
                # Generate a unique username
                username = generate_username(name)
                
                # Check if a user with this username already exists
                if User.query.filter_by(username=username).first():
                    continue
                
                # Generate email
                email = f"{username}@example.com"
                
                # Create new user
                user = User()
                user.username = username
                user.email = email
                user.role = 'doctor'
                user.first_name = first_name
                user.last_name = last_name
                # Set is_active through __setattr__ to avoid property error
                setattr(user, 'is_active', True)
                user.created_at = datetime.utcnow()
                user.set_password('Doctor123!')
                
                db.session.add(user)
                db.session.flush()  # Generate ID
                
                # Create doctor info
                years = doctor_data.get("years", 5)
                if years is None:
                    years = 5
                    
                bio = f"Located in {doctor_data['area']} with {years} years of experience. "
                bio += f"Rating: {doctor_data['rating']}/5.0. "
                if doctor_data.get("contact"):
                    bio += f"Contact: {doctor_data['contact']}."
                    
                doctor_info = DoctorInfo()
                doctor_info.user_id = user.id
                doctor_info.specialization = random.choice(specializations)
                doctor_info.qualification = random.choice(qualifications)
                doctor_info.experience_years = years
                doctor_info.bio = bio
                doctor_info.is_approved = True
                
                db.session.add(doctor_info)
            
            # Commit all changes
            db.session.commit()
            print("Doctors added successfully!")
            
    except Exception as e:
        print(f"Error adding doctors: {e}")
        db.session.rollback()

if __name__ == "__main__":
    add_doctors()