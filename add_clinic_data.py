from app import app, db
from models import User, DoctorInfo
import random
from datetime import datetime

# Doctor data from the provided table
doctors_data = [
    {"name": "Dr. Amarpreet", "rating": 4.9, "area": "Kamla Nagar", "years": 13, "contact": "08401732925"},
    {"name": "Dr. Apoorv Yadav", "rating": 4.8, "area": "Delhi Gate", "years": 8, "contact": "08460249428"},
    {"name": "Dr. Sarang Dhar", "rating": 4.7, "area": "Gandhi Nagar", "years": 24, "contact": "08511494425"},
    {"name": "Dr. Pallavee Walia", "rating": 4.6, "area": "Dayal Bagh", "years": 9, "contact": ""},
    {"name": "Dr. Chinu Agrawal", "rating": 4.9, "area": "Sikandra", "years": 25, "contact": ""},
    {"name": "Dr. Mohit Jain", "rating": 4.8, "area": "Taj Nagari", "years": 3, "contact": ""},
    {"name": "Dr. Prabhat Sharma", "rating": 4.9, "area": "Hari Parbat", "years": 13, "contact": ""}
]

# Specialization options
specializations = [
    "Clinical Psychology", 
    "Counseling Psychology", 
    "Neuropsychology", 
    "Health Psychology", 
    "Child Psychology"
]

# Qualification options
qualifications = [
    "Ph.D. in Psychology",
    "M.Phil in Clinical Psychology",
    "Master's in Counseling Psychology",
    "M.D. in Psychiatry"
]

def create_doctor_users():
    with app.app_context():
        for data in doctors_data:
            # Parse the name
            name_parts = data["name"].split()
            
            # Skip the 'Dr.' prefix
            if name_parts[0] == "Dr.":
                first_name = name_parts[1]
                last_name = " ".join(name_parts[2:]) if len(name_parts) > 2 else ""
            else:
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:])
            
            # Create username (simple format)
            username = f"{first_name.lower()}_{last_name.lower()}".replace(" ", "")
            # Check if this username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"User {username} already exists, skipping...")
                continue
                
            # Create email
            email = f"{username}@example.com"
            
            # Create and save the user
            user = User()
            user.username = username
            user.email = email
            user.role = 'doctor'
            user.first_name = first_name
            user.last_name = last_name
            user.created_at = datetime.utcnow()
            user.set_password('Doctor123!')
            
            db.session.add(user)
            db.session.flush()  # Generate the user ID
            
            # Create the doctor info
            doc_info = DoctorInfo()
            doc_info.user_id = user.id
            doc_info.specialization = random.choice(specializations)
            doc_info.qualification = random.choice(qualifications)
            doc_info.experience_years = data.get("years", 5)
            
            # Create a detailed bio
            bio = f"Based in {data['area']} with {data.get('years', 'several')} years of experience. "
            bio += f"Patient rating: {data['rating']}/5.0. "
            if data.get("contact"):
                bio += f"Contact: {data['contact']}."
            
            doc_info.bio = bio
            doc_info.is_approved = True  # Pre-approve these doctors
            
            db.session.add(doc_info)
            
        # Save all changes
        db.session.commit()
        print(f"Added {len(doctors_data)} doctors to the database.")

if __name__ == "__main__":
    create_doctor_users()