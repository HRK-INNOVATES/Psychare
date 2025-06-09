#!/usr/bin/env python3
"""
Comprehensive fix for all database constructor issues and errors
"""
import re

def fix_routes_file():
    with open('routes.py', 'r') as f:
        content = f.read()
    
    # Fix CallSession constructors - first occurrence (line 307)
    content = re.sub(
        r'call_session = CallSession\(appointment_id=appointment\.id, status=\'scheduled\'\)',
        'call_session = CallSession()\n        call_session.appointment_id = appointment.id\n        call_session.status = \'scheduled\'',
        content,
        count=1
    )
    
    # Fix CallSession constructors - second occurrence (line 609)
    content = re.sub(
        r'call_session = CallSession\(appointment_id=appointment\.id, status=\'scheduled\'\)',
        'call_session = CallSession()\n        call_session.appointment_id = appointment.id\n        call_session.status = \'scheduled\'',
        content
    )
    
    # Fix Complaint constructor
    content = re.sub(
        r'complaint = Complaint\(\s*patient_id=current_user\.patient_info\.id,\s*subject=form\.subject\.data,\s*description=form\.description\.data\s*\)',
        'complaint = Complaint()\n    complaint.patient_id = current_user.patient_info.id\n    complaint.subject = form.subject.data\n    complaint.description = form.description.data',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Fix Availability constructors
    content = re.sub(
        r'availability = Availability\([^)]*\)',
        lambda m: 'availability = Availability()\n' + re.sub(r'(\w+)=([^,\)]+)', r'        availability.\1 = \2', m.group(0)[19:-1]),
        content
    )
    
    # Fix PatientReport constructor
    content = re.sub(
        r'report = PatientReport\([^)]*\)',
        lambda m: 'report = PatientReport()\n' + re.sub(r'(\w+)=([^,\)]+)', r'    report.\1 = \2', m.group(0)[18:-1]),
        content
    )
    
    # Fix SliderImage constructor
    content = re.sub(
        r'slider_image = SliderImage\([^)]*\)',
        lambda m: 'slider_image = SliderImage()\n' + re.sub(r'(\w+)=([^,\)]+)', r'    slider_image.\1 = \2', m.group(0)[21:-1]),
        content
    )
    
    # Fix ChatMessage constructor
    content = re.sub(
        r'message = ChatMessage\([^)]*\)',
        lambda m: 'message = ChatMessage()\n' + re.sub(r'(\w+)=([^,\)]+)', r'    message.\1 = \2', m.group(0)[17:-1]),
        content
    )
    
    # Fix ChatConversation constructor
    content = re.sub(
        r'conversation = ChatConversation\([^)]*\)',
        lambda m: 'conversation = ChatConversation()\n' + re.sub(r'(\w+)=([^,\)]+)', r'    conversation.\1 = \2', m.group(0)[25:-1]),
        content
    )
    
    with open('routes.py', 'w') as f:
        f.write(content)

def fix_models_file():
    with open('models.py', 'r') as f:
        content = f.read()
    
    # Fix is_active override issue
    content = content.replace(
        'is_active = db.Column(db.Boolean, default=True)',
        'active = db.Column(db.Boolean, default=True)'
    )
    
    with open('models.py', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    fix_routes_file()
    fix_models_file()
    print("Fixed all database constructor issues and model conflicts")