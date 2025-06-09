import os
from datetime import datetime, time, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import pdfkit

from app import app, db
from models import User, DoctorInfo, PatientInfo, Availability, Appointment, CallSession, PatientReport, Complaint, SliderImage, ChatConversation, ChatMessage
from forms import AvailabilityForm, BookAppointmentForm, ComplaintForm, PatientReportForm, SliderImageForm, ChatMessageForm
from utils import get_availability_slots, create_pdf_report

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False


# Common routes
@app.route('/')
def index():
    sliders = SliderImage.query.filter_by(is_active=True).order_by(SliderImage.display_order).all()
    doctors = User.query.join(DoctorInfo).filter(User.role == 'doctor', DoctorInfo.is_approved == True).all()
    return render_template('index.html', sliders=sliders, doctors=doctors)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


# Patient routes
@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient_info.id
    ).filter(
        Appointment.appointment_date >= datetime.now().date(),
        Appointment.status.in_(['pending', 'confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.start_time).limit(5).all()
    
    # Get recent reports
    recent_reports = PatientReport.query.filter_by(
        patient_id=current_user.patient_info.id
    ).order_by(PatientReport.report_date.desc()).limit(3).all()
    
    return render_template('patient/dashboard.html', 
                           appointments=upcoming_appointments, 
                           reports=recent_reports,
                           today=datetime.now().date())


@app.route('/patient/doctors')
@login_required
def patient_doctors():
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all approved doctors
    doctors = User.query.join(DoctorInfo).filter(
        User.role == 'doctor',
        DoctorInfo.is_approved == True
    ).all()
    
    # Get specializations for filtering
    specializations = db.session.query(DoctorInfo.specialization).distinct().all()
    specializations = [s[0] for s in specializations]
    
    return render_template('patient/doctors.html', 
                           doctors=doctors, 
                           specializations=specializations)


@app.route('/patient/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(doctor_id):
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get doctor info
    doctor_info = DoctorInfo.query.filter_by(id=doctor_id).first_or_404()
    doctor = User.query.get(doctor_info.user_id)
    
    form = BookAppointmentForm()
    
    # Populate time slot choices if appointment date is provided (for both GET and POST)
    appointment_date = None
    if request.method == 'POST':
        # Try to get date from form data first
        appointment_date = form.appointment_date.data
    elif request.method == 'GET':
        date_param = request.args.get('date')
        if date_param:
            try:
                appointment_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                appointment_date = None
    
    if appointment_date:
        selected_date = appointment_date
        day_of_week = selected_date.weekday()  # 0 = Monday, 6 = Sunday
        
        # Get doctor's availability for this day
        availabilities = Availability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_active=True,
            is_recurring=True
        ).all()
        
        # Also check for specific date availability
        specific_availabilities = Availability.query.filter_by(
            doctor_id=doctor_id,
            specific_date=selected_date,
            is_active=True,
            is_recurring=False
        ).all()
        
        availabilities.extend(specific_availabilities)
        
        # Get existing appointments for this doctor on this date
        existing_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=selected_date
        ).filter(
            Appointment.status.in_(['pending', 'confirmed'])
        ).all()
        
        # Calculate available slots and populate form choices
        available_slots = get_availability_slots(availabilities, existing_appointments)
        form.start_time.choices = [(slot, slot) for slot in available_slots]
    
    # If form is submitted
    if form.validate_on_submit():
        # Extract time range from the selected option
        time_range = form.start_time.data.split('-')
        start_time = datetime.strptime(time_range[0].strip(), '%H:%M').time()
        end_time = datetime.strptime(time_range[1].strip(), '%H:%M').time()
        
        # Create new appointment
        appointment = Appointment()
        appointment.doctor_id = doctor_info.id
        appointment.patient_id = current_user.patient_info.id
        appointment.appointment_date = form.appointment_date.data
        appointment.start_time = start_time
        appointment.end_time = end_time
        appointment.notes = form.notes.data
        appointment.status = 'pending'
        db.session.add(appointment)
        db.session.commit()
        
        # Create call session for this appointment
        call_session = CallSession()
        call_session.appointment_id = appointment.id
        call_session.status = 'scheduled'
        db.session.add(call_session)
        db.session.commit()
        
        # Show success animation instead of redirecting immediately
        return render_template('patient/appointment_success.html', 
                             appointment=appointment,
                             doctor=doctor)
    
    return render_template('patient/book_appointment.html', 
                           form=form, 
                           doctor=doctor,
                           doctor_info=doctor_info)


@app.route('/patient/get_available_slots', methods=['POST'])
@login_required
def get_available_slots():
    if not current_user.is_patient():
        return jsonify({'error': 'Access denied'}), 403
    
    doctor_id = request.form.get('doctor_id')
    date_str = request.form.get('date')
    
    if not doctor_id or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day_of_week = selected_date.weekday()  # 0 = Monday, 6 = Sunday
        
        # Get doctor's availability for this day
        availabilities = Availability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_active=True
        ).all()
        
        if not availabilities:
            return jsonify({'available_slots': []})
        
        # Get existing appointments for this doctor on this date
        existing_appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=selected_date
        ).filter(
            Appointment.status.in_(['pending', 'confirmed'])
        ).all()
        
        # Calculate available slots
        available_slots = get_availability_slots(availabilities, existing_appointments)
        
        return jsonify({'available_slots': available_slots})
    
    except Exception as e:
        app.logger.error(f"Error getting available slots: {str(e)}")
        return jsonify({'error': 'Failed to get available slots'}), 500


@app.route('/patient/appointments')
@login_required
def patient_appointments():
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient_info.id
    ).filter(
        Appointment.appointment_date >= datetime.now().date()
    ).order_by(Appointment.appointment_date, Appointment.start_time).all()
    
    past_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient_info.id
    ).filter(
        Appointment.appointment_date < datetime.now().date()
    ).order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc()).all()
    
    return render_template('patient/appointments.html', 
                           upcoming_appointments=upcoming_appointments, 
                           past_appointments=past_appointments,
                           today=datetime.now().date())


@app.route('/patient/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if this appointment belongs to the current patient
    if appointment.patient_id != current_user.patient_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('patient_appointments'))
    
    # Check if the appointment can be cancelled
    if appointment.status in ['cancelled', 'completed']:
        flash('This appointment cannot be cancelled.', 'warning')
        return redirect(url_for('patient_appointments'))
    
    # Cancel the appointment
    appointment.status = 'cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully', 'success')
    return redirect(url_for('patient_appointments'))


@app.route('/patient/join_call/<int:appointment_id>')
@login_required
def patient_join_call(appointment_id):
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if this appointment belongs to the current patient
    if appointment.patient_id != current_user.patient_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('patient_appointments'))
    
    # Check if the appointment is scheduled for today
    if appointment.appointment_date != datetime.now().date():
        flash('This appointment is not scheduled for today', 'warning')
        return redirect(url_for('patient_appointments'))
    
    # Check if it's time for the appointment
    current_time = datetime.now().time()
    start_time = appointment.start_time
    
    # Allow joining 5 minutes before the start time
    join_time = datetime.combine(datetime.today(), start_time) - timedelta(minutes=5)
    if datetime.now() < join_time:
        flash('It\'s not time for this appointment yet', 'warning')
        return redirect(url_for('patient_appointments'))
    
    # Get call session
    call_session = CallSession.query.filter_by(appointment_id=appointment.id).first()
    if not call_session:
        call_session = CallSession()
        call_session.appointment_id = appointment.id
        call_session.status = 'scheduled'
        db.session.add(call_session)
        db.session.commit()
    
    # Update call session status
    if call_session.status == 'scheduled':
        call_session.status = 'in_progress'
        call_session.start_time = datetime.now()
        db.session.commit()
    
    # Get doctor details
    doctor = User.query.get(appointment.doctor_info.user_id)
    
    return render_template('patient/call.html', 
                           appointment=appointment, 
                           call_session=call_session,
                           doctor=doctor)


@app.route('/patient/reports')
@login_required
def patient_reports():
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    reports = PatientReport.query.filter_by(
        patient_id=current_user.patient_info.id
    ).order_by(PatientReport.report_date.desc()).all()
    
    return render_template('patient/report.html', reports=reports)


@app.route('/patient/view_report/<int:report_id>')
@login_required
def view_patient_report(report_id):
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    report = PatientReport.query.get_or_404(report_id)
    
    # Check if this report belongs to the current patient
    if report.patient_id != current_user.patient_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('patient_reports'))
    
    # Get doctor details
    doctor = User.query.get(report.doctor.user_id)
    
    return render_template('patient/view_report.html', report=report, doctor=doctor)


@app.route('/patient/complaint', methods=['GET', 'POST'])
@login_required
def patient_complaint():
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ComplaintForm()
    
    if form.validate_on_submit():
        complaint = Complaint()
        complaint.patient_id = current_user.patient_info.id
        complaint.subject = form.subject.data
        complaint.description = form.description.data
        complaint.status = 'open'
        db.session.add(complaint)
        db.session.commit()
        
        flash('Your complaint has been submitted successfully', 'success')
        return redirect(url_for('patient_dashboard'))
    
    # Get past complaints
    complaints = Complaint.query.filter_by(
        patient_id=current_user.patient_info.id
    ).order_by(Complaint.created_at.desc()).all()
    
    return render_template('patient/complaint.html', form=form, complaints=complaints)


# Doctor routes
@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if doctor is approved
    if not current_user.doctor_info.is_approved:
        flash('Your account is pending approval from admin', 'warning')
        return redirect(url_for('logout'))
    
    # Get today's appointments
    today_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_info.id,
        appointment_date=datetime.now().date(),
        status='confirmed'
    ).order_by(Appointment.start_time).all()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_info.id
    ).filter(
        Appointment.appointment_date > datetime.now().date(),
        Appointment.status.in_(['pending', 'confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.start_time).limit(5).all()
    
    # Get pending appointments
    pending_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_info.id,
        status='pending'
    ).all()
    
    return render_template('doctor/dashboard.html', 
                           today_appointments=today_appointments, 
                           upcoming_appointments=upcoming_appointments,
                           pending_appointments=pending_appointments)


@app.route('/doctor/availability', methods=['GET', 'POST'])
@login_required
def doctor_availability():
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    form = AvailabilityForm()
    
    if form.validate_on_submit():
        from datetime import time
        
        # Clear existing availability for the same day/date to avoid conflicts
        if form.availability_type.data == 'recurring':
            Availability.query.filter_by(
                doctor_id=current_user.doctor_info.id,
                day_of_week=form.day_of_week.data,
                is_recurring=True
            ).delete()
        else:
            Availability.query.filter_by(
                doctor_id=current_user.doctor_info.id,
                specific_date=form.specific_date.data,
                is_recurring=False
            ).delete()
        
        # Create availability for each selected time slot
        slot_count = 0
        if form.time_slots.data:
            for time_slot in form.time_slots.data:
                hour = int(time_slot.split(':')[0])
                start_time = time(hour, 0)
                end_time = time(hour + 1, 0)
                
                if form.availability_type.data == 'recurring':
                    availability = Availability()
                    availability.doctor_id = current_user.doctor_info.id
                    availability.day_of_week = form.day_of_week.data
                    availability.specific_date = None
                    availability.start_time = start_time
                    availability.end_time = end_time
                    availability.is_active = True
                    availability.is_recurring = True
                else:  # specific date
                    availability = Availability()
                    availability.doctor_id = current_user.doctor_info.id
                    availability.day_of_week = None
                    availability.specific_date = form.specific_date.data
                    availability.start_time = start_time
                    availability.end_time = end_time
                    availability.is_active = True
                    availability.is_recurring = False
                
                db.session.add(availability)
                slot_count += 1
        
        db.session.commit()
        
        if form.availability_type.data == 'recurring':
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][form.day_of_week.data]
            success_msg = f'{slot_count} time slots added for {day_name}'
        else:
            date_str = form.specific_date.data.strftime("%B %d, %Y") if form.specific_date.data else "selected date"
            success_msg = f'{slot_count} time slots added for {date_str}'
        
        flash(success_msg, 'success')
        return redirect(url_for('doctor_availability'))
    
    # Get current availability - both recurring and specific dates
    recurring_availabilities = Availability.query.filter_by(
        doctor_id=current_user.doctor_info.id,
        is_recurring=True
    ).order_by(Availability.day_of_week, Availability.start_time).all()
    
    specific_availabilities = Availability.query.filter_by(
        doctor_id=current_user.doctor_info.id,
        is_recurring=False
    ).order_by(Availability.specific_date, Availability.start_time).all()
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Add today's date for filtering specific availabilities in the template
    today = datetime.now().date()
    
    return render_template('doctor/availability.html', 
                           form=form, 
                           recurring_availabilities=recurring_availabilities,
                           specific_availabilities=specific_availabilities,
                           today=today,
                           days=days)


@app.route('/doctor/delete_availability/<int:availability_id>', methods=['POST'])
@login_required
def delete_availability(availability_id):
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    availability = Availability.query.get_or_404(availability_id)
    
    # Check if this availability belongs to the current doctor
    if availability.doctor_id != current_user.doctor_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor_availability'))
    
    db.session.delete(availability)
    db.session.commit()
    
    flash('Availability deleted successfully', 'success')
    return redirect(url_for('doctor_availability'))


@app.route('/doctor/appointments')
@login_required
def doctor_appointments():
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all appointments
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_info.id
    ).order_by(Appointment.appointment_date.desc(), Appointment.start_time).all()
    
    from datetime import date
    today = date.today()
    return render_template('doctor/appointments.html', appointments=appointments, today=today)


@app.route('/doctor/update_appointment_status/<int:appointment_id>', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if this appointment belongs to the current doctor
    if appointment.doctor_id != current_user.doctor_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    status = request.form.get('status')
    if status not in ['pending', 'confirmed', 'cancelled', 'completed']:
        flash('Invalid status', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    appointment.status = status
    db.session.commit()
    
    flash('Appointment status updated successfully', 'success')
    return redirect(url_for('doctor_appointments'))


@app.route('/doctor/join_call/<int:appointment_id>')
@login_required
def doctor_join_call(appointment_id):
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if this appointment belongs to the current doctor
    if appointment.doctor_id != current_user.doctor_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    # Check if the appointment is confirmed and scheduled for today
    if appointment.status != 'confirmed' or appointment.appointment_date != datetime.now().date():
        flash('This appointment is not confirmed or not scheduled for today', 'warning')
        return redirect(url_for('doctor_appointments'))
    
    # Get call session
    call_session = CallSession.query.filter_by(appointment_id=appointment.id).first()
    if not call_session:
        call_session = CallSession()
        call_session.appointment_id = appointment.id
        call_session.status = 'scheduled'
        db.session.add(call_session)
        db.session.commit()
    
    # Update call session status
    if call_session.status == 'scheduled':
        call_session.status = 'in_progress'
        call_session.start_time = datetime.now()
        db.session.commit()
    
    # Get patient details
    patient = User.query.get(appointment.patient_info.user_id)
    
    return render_template('doctor/call.html', 
                           appointment=appointment, 
                           call_session=call_session,
                           patient=patient)


@app.route('/doctor/end_call/<int:appointment_id>', methods=['POST'])
@login_required
def end_call(appointment_id):
    if not current_user.is_doctor() and not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    call_session = CallSession.query.filter_by(appointment_id=appointment.id).first_or_404()
    
    # Check if the user is authorized
    if current_user.is_doctor() and appointment.doctor_id != current_user.doctor_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    if current_user.is_patient() and appointment.patient_id != current_user.patient_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('patient_appointments'))
    
    # End the call session
    call_session.status = 'completed'
    call_session.end_time = datetime.now()
    call_session.recording_path = f"recording_{appointment.id}.mp3"  # Mock recording path
    
    # Update appointment status
    appointment.status = 'completed'
    
    db.session.commit()
    
    flash('Call ended successfully', 'success')
    
    # Redirect based on user role
    if current_user.is_doctor():
        return redirect(url_for('doctor_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))


@app.route('/doctor/patient_report/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def create_patient_report(appointment_id):
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if this appointment belongs to the current doctor
    if appointment.doctor_id != current_user.doctor_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    # Check if this appointment is completed
    if appointment.status != 'completed':
        flash('Cannot create report for incomplete appointment', 'warning')
        return redirect(url_for('doctor_appointments'))
    
    # Get patient details
    patient = User.query.get(appointment.patient_info.user_id)
    
    form = PatientReportForm()
    
    if form.validate_on_submit():
        # Check if report already exists
        existing_report = PatientReport.query.filter_by(appointment_id=appointment.id).first()
        
        if existing_report:
            # Update existing report
            existing_report.diagnosis = form.diagnosis.data
            existing_report.treatment_plan = form.treatment_plan.data
            existing_report.recommendations = form.recommendations.data
            existing_report.next_appointment = form.next_appointment.data
            report = existing_report
        else:
            # Create new report
            report = PatientReport()
            report.patient_id = appointment.patient_id
            report.doctor_id = appointment.doctor_id
            report.appointment_id = appointment.id
            report.diagnosis = form.diagnosis.data
            report.treatment_plan = form.treatment_plan.data
            report.recommendations = form.recommendations.data
            report.next_appointment = form.next_appointment.data
            db.session.add(report)
        
        db.session.commit()
        
        # Generate PDF report
        pdf_filename = f"report_{report.id}.pdf"
        static_folder = app.static_folder if app.static_folder else 'static'
        pdf_path = os.path.join(static_folder, 'reports', pdf_filename)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        # Create PDF using the utility function
        create_pdf_report(report, patient, current_user, pdf_path)
        
        # Update report with PDF path
        report.pdf_path = pdf_filename
        db.session.commit()
        
        flash('Patient report created successfully', 'success')
        return redirect(url_for('doctor_appointments'))
    
    # Pre-fill form if report exists
    existing_report = PatientReport.query.filter_by(appointment_id=appointment.id).first()
    if existing_report:
        form.diagnosis.data = existing_report.diagnosis
        form.treatment_plan.data = existing_report.treatment_plan
        form.recommendations.data = existing_report.recommendations
        form.next_appointment.data = existing_report.next_appointment
    
    return render_template('doctor/patient_report.html', 
                           form=form, 
                           appointment=appointment,
                           patient=patient)


@app.route('/doctor/view_patient_report/<int:report_id>')
@login_required
def doctor_view_patient_report(report_id):
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    report = PatientReport.query.get_or_404(report_id)
    
    # Check if this report was created by the current doctor
    if report.doctor_id != current_user.doctor_info.id:
        flash('Access denied', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    # Get patient details
    patient = User.query.get(report.patient.user_id)
    
    return render_template('doctor/view_patient_report.html', 
                           report=report, 
                           patient=patient)


# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Count statistics
    total_patients = User.query.filter_by(role='patient').count()
    total_doctors = User.query.filter_by(role='doctor').count()
    total_appointments = Appointment.query.count()
    pending_doctors = DoctorInfo.query.filter_by(is_approved=False).count()
    open_complaints = Complaint.query.filter_by(status='open').count()
    
    # Get recent appointments
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           total_appointments=total_appointments,
                           pending_doctors=pending_doctors,
                           open_complaints=open_complaints,
                           recent_appointments=recent_appointments)


@app.route('/admin/doctors')
@login_required
def admin_doctors():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all doctors
    doctors = User.query.filter_by(role='doctor').order_by(User.created_at.desc()).all()
    
    return render_template('admin/doctors.html', doctors=doctors)


@app.route('/admin/approve_doctor/<int:doctor_id>', methods=['POST'])
@login_required
def approve_doctor(doctor_id):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first_or_404()
    doctor_info = DoctorInfo.query.filter_by(user_id=doctor.id).first_or_404()
    
    doctor_info.is_approved = True
    db.session.commit()
    
    flash(f'Doctor {doctor.username} has been approved', 'success')
    return redirect(url_for('admin_doctors'))


@app.route('/admin/reject_doctor/<int:doctor_id>', methods=['POST'])
@login_required
def reject_doctor(doctor_id):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first_or_404()
    doctor_info = DoctorInfo.query.filter_by(user_id=doctor.id).first_or_404()
    
    # Delete doctor
    db.session.delete(doctor)
    db.session.commit()
    
    flash(f'Doctor {doctor.username} has been rejected and deleted', 'success')
    return redirect(url_for('admin_doctors'))


@app.route('/admin/patients')
@login_required
def admin_patients():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all patients
    patients = User.query.filter_by(role='patient').order_by(User.created_at.desc()).all()
    
    return render_template('admin/patients.html', patients=patients)


@app.route('/admin/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Toggle active status
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'blocked' if not user.is_active else 'unblocked'
    flash(f'User {user.username} has been {status}', 'success')
    
    # Redirect based on user role
    if user.role == 'doctor':
        return redirect(url_for('admin_doctors'))
    else:
        return redirect(url_for('admin_patients'))


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Cannot delete admin
    if user.role == 'admin':
        flash('Cannot delete admin user', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Get redirect URL before deleting
    redirect_url = url_for('admin_patients') if user.role == 'patient' else url_for('admin_doctors')
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} has been deleted', 'success')
    return redirect(redirect_url)


@app.route('/admin/appointments')
@login_required
def admin_appointments():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all appointments
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc(), Appointment.start_time).all()
    
    return render_template('admin/appointments.html', appointments=appointments)


@app.route('/admin/complaints')
@login_required
def admin_complaints():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all complaints
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    
    return render_template('admin/complaints.html', complaints=complaints)


@app.route('/admin/update_complaint/<int:complaint_id>', methods=['POST'])
@login_required
def update_complaint(complaint_id):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    complaint = Complaint.query.get_or_404(complaint_id)
    
    status = request.form.get('status')
    admin_response = request.form.get('admin_response')
    
    if status not in ['open', 'under_review', 'resolved', 'closed']:
        flash('Invalid status', 'danger')
        return redirect(url_for('admin_complaints'))
    
    complaint.status = status
    complaint.admin_response = admin_response
    
    if status in ['resolved', 'closed']:
        complaint.resolved_at = datetime.now()
    
    db.session.commit()
    
    flash('Complaint updated successfully', 'success')
    return redirect(url_for('admin_complaints'))


@app.route('/admin/recordings')
@login_required
def admin_recordings():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all completed call sessions with recordings
    call_sessions = CallSession.query.filter_by(status='completed').filter(CallSession.recording_path != None).all()
    
    return render_template('admin/recordings.html', call_sessions=call_sessions)


@app.route('/admin/slider', methods=['GET', 'POST'])
@login_required
def admin_slider():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    form = SliderImageForm()
    
    if form.validate_on_submit():
        slider = SliderImage()
        slider.title = form.title.data
        slider.description = form.description.data
        slider.image_url = form.image_url.data
        slider.display_order = form.display_order.data
        slider.is_active = form.is_active.data
        db.session.add(slider)
        db.session.commit()
        
        flash('Slider image added successfully', 'success')
        return redirect(url_for('admin_slider'))
    
    # Get all slider images
    sliders = SliderImage.query.order_by(SliderImage.display_order).all()
    
    return render_template('admin/slider.html', form=form, sliders=sliders)


@app.route('/admin/delete_slider/<int:slider_id>', methods=['POST'])
@login_required
def delete_slider(slider_id):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    slider = SliderImage.query.get_or_404(slider_id)
    
    db.session.delete(slider)
    db.session.commit()
    
    flash('Slider image deleted successfully', 'success')
    return redirect(url_for('admin_slider'))


# Chat functionality routes
@app.route('/patient/chat')
@login_required
def patient_chat():
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get patient's conversations with doctors
    conversations = db.session.query(ChatConversation).join(
        PatientInfo, ChatConversation.patient_id == PatientInfo.id
    ).filter(PatientInfo.user_id == current_user.id).order_by(
        ChatConversation.last_message_at.desc()
    ).all()
    
    return render_template('patient/chat.html', conversations=conversations)


@app.route('/doctor/chat')
@login_required
def doctor_chat():
    if not current_user.is_doctor():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get doctor's conversations with patients
    conversations = db.session.query(ChatConversation).join(
        DoctorInfo, ChatConversation.doctor_id == DoctorInfo.id
    ).filter(DoctorInfo.user_id == current_user.id).order_by(
        ChatConversation.last_message_at.desc()
    ).all()
    
    return render_template('doctor/chat.html', conversations=conversations)


@app.route('/chat/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
def chat_conversation(conversation_id):
    conversation = ChatConversation.query.get_or_404(conversation_id)
    
    # Check if user has access to this conversation
    if current_user.is_patient():
        if conversation.patient.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('patient_chat'))
    elif current_user.is_doctor():
        if conversation.doctor.user_id != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('doctor_chat'))
    else:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Mark messages as read for the current user
    unread_messages = ChatMessage.query.filter_by(
        conversation_id=conversation_id,
        is_read=False
    ).filter(ChatMessage.sender_id != current_user.id).all()
    
    for message in unread_messages:
        message.is_read = True
    db.session.commit()
    
    form = ChatMessageForm()
    
    if form.validate_on_submit():
        message = ChatMessage()
        message.conversation_id = conversation_id
        message.sender_id = current_user.id
        message.message_text = form.message_text.data
        db.session.add(message)
        
        # Update conversation last message time
        conversation.last_message_at = datetime.utcnow()
        db.session.commit()
        
        form.message_text.data = ''  # Clear the form
        flash('Message sent successfully', 'success')
        return redirect(url_for('chat_conversation', conversation_id=conversation_id))
    
    messages = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.created_at).all()
    
    return render_template('chat/conversation.html', conversation=conversation, messages=messages, form=form)


@app.route('/start_chat/<int:doctor_id>')
@login_required
def start_chat_with_doctor(doctor_id):
    if not current_user.is_patient():
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    doctor = DoctorInfo.query.get_or_404(doctor_id)
    patient = PatientInfo.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found', 'danger')
        return redirect(url_for('patient_dashboard'))
    
    # Check if conversation already exists
    existing_conversation = ChatConversation.query.filter_by(
        patient_id=patient.id,
        doctor_id=doctor.id
    ).first()
    
    if existing_conversation:
        return redirect(url_for('chat_conversation', conversation_id=existing_conversation.id))
    
    # Create new conversation
    conversation = ChatConversation()
    conversation.patient_id = patient.id
    conversation.doctor_id = doctor.id
    db.session.add(conversation)
    db.session.commit()
    
    return redirect(url_for('chat_conversation', conversation_id=conversation.id))


@app.route('/api/chat/messages/<int:conversation_id>')
@login_required
def get_chat_messages(conversation_id):
    conversation = ChatConversation.query.get_or_404(conversation_id)
    
    # Check access
    if current_user.is_patient() and conversation.patient.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    elif current_user.is_doctor() and conversation.doctor.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    messages = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.created_at).all()
    
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'sender_name': message.sender.get_full_name(),
            'sender_id': message.sender_id,
            'message_text': message.message_text,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_current_user': message.sender_id == current_user.id
        })
    
    return jsonify({'messages': messages_data})


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code=403, error_message='Access forbidden'), 403


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500


def generate_pdf_report(report_data):
    if not PDFKIT_AVAILABLE:
        flash("PDF generation is not available. Please install wkhtmltopdf.", "warning")
        return None
        
    try:
        # Rest of the PDF generation code
        return pdfkit.from_string(html_content, False)
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return None
