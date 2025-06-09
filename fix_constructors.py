#!/usr/bin/env python3
"""
Fix all database model constructor issues in routes.py
"""

def fix_constructors():
    with open('routes.py', 'r') as f:
        content = f.read()
    
    # Fix all CallSession constructors
    content = content.replace(
        'call_session = CallSession(appointment_id=appointment.id, status=\'scheduled\')',
        'call_session = CallSession()\n        call_session.appointment_id = appointment.id\n        call_session.status = \'scheduled\''
    )
    
    # Fix Complaint constructors
    content = content.replace(
        'complaint = Complaint(',
        'complaint = Complaint()\n    complaint.'
    ).replace(
        'patient_id=current_user.patient_info.id,',
        'patient_id = current_user.patient_info.id\n    complaint.'
    ).replace(
        'subject=form.subject.data,',
        'subject = form.subject.data\n    complaint.'
    ).replace(
        'description=form.description.data',
        'description = form.description.data'
    )
    
    # Fix Availability constructors
    content = content.replace(
        'availability = Availability(',
        'availability = Availability()\n        availability.'
    )
    
    # Fix PatientReport constructors
    content = content.replace(
        'report = PatientReport(',
        'report = PatientReport()\n    report.'
    )
    
    # Fix SliderImage constructors
    content = content.replace(
        'slider_image = SliderImage(',
        'slider_image = SliderImage()\n    slider_image.'
    )
    
    # Fix ChatMessage constructors
    content = content.replace(
        'message = ChatMessage(',
        'message = ChatMessage()\n    message.'
    )
    
    # Fix ChatConversation constructors
    content = content.replace(
        'conversation = ChatConversation(',
        'conversation = ChatConversation()\n    conversation.'
    )
    
    with open('routes.py', 'w') as f:
        f.write(content)
    
    print("Fixed all database constructor issues")

if __name__ == '__main__':
    fix_constructors()