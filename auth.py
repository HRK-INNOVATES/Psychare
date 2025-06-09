from flask import request, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
from datetime import datetime

from app import app, db
from models import User, DoctorInfo, PatientInfo
from forms import LoginForm, PatientRegistrationForm, DoctorRegistrationForm


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register/patient', methods=['GET', 'POST'])
def register_patient():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = PatientRegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='patient'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Get user ID before committing
        
        patient_info = PatientInfo(
            user_id=user.id,
            dob=form.dob.data,
            gender=form.gender.data,
            contact_number=form.contact_number.data
        )
        db.session.add(patient_info)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    today = datetime.now().date().strftime('%Y-%m-%d')
    return render_template('register.html', title='Register as Patient', form=form, user_type='patient', today=today)


@app.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = DoctorRegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='doctor'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Get user ID before committing
        
        doctor_info = DoctorInfo(
            user_id=user.id,
            specialization=form.specialization.data,
            qualification=form.qualification.data,
            experience_years=form.experience_years.data,
            bio=form.bio.data,
            is_approved=False  # Doctors need approval from admin
        )
        db.session.add(doctor_info)
        db.session.commit()
        
        flash('Your account has been created! You need admin approval before you can log in.', 'info')
        return redirect(url_for('login'))
    
    today = datetime.now().date().strftime('%Y-%m-%d')
    return render_template('register.html', title='Register as Doctor', form=form, user_type='doctor', today=today)


@app.route('/dashboard')
@login_required
def dashboard():
    """Redirect to appropriate dashboard based on user role"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_doctor():
        # Check if doctor is approved
        if not current_user.doctor_info.is_approved:
            flash('Your account is pending approval from admin.', 'warning')
            logout_user()
            return redirect(url_for('login'))
        return redirect(url_for('doctor_dashboard'))
    elif current_user.is_patient():
        return redirect(url_for('patient_dashboard'))
    else:
        flash('Invalid user role', 'danger')
        return redirect(url_for('logout'))
