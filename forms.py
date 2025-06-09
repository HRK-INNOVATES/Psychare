from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField, DateField, TimeField, RadioField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from datetime import date, datetime

from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class PatientRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    dob = DateField('Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')
    
    def validate_dob(self, dob):
        if dob.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')

class DoctorRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=100)])
    qualification = StringField('Qualification', validators=[DataRequired(), Length(max=200)])
    experience_years = IntegerField('Years of Experience', validators=[DataRequired()])
    bio = TextAreaField('Professional Bio', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class AvailabilityForm(FlaskForm):
    availability_type = RadioField('Availability Type', 
                                  choices=[('recurring', 'Weekly Recurring'), ('specific', 'Specific Date')],
                                  default='recurring',
                                  validators=[DataRequired()])
    day_of_week = SelectField('Day of Week', choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ], coerce=int, validators=[Optional()])
    specific_date = DateField('Specific Date', format='%Y-%m-%d', validators=[Optional()])
    time_slots = SelectMultipleField('Available Time Slots', 
                                   choices=[
                                       ('10:00', '10:00 AM - 11:00 AM'),
                                       ('11:00', '11:00 AM - 12:00 PM'),
                                       ('12:00', '12:00 PM - 1:00 PM'),
                                       ('13:00', '1:00 PM - 2:00 PM'),
                                       ('14:00', '2:00 PM - 3:00 PM'),
                                       ('15:00', '3:00 PM - 4:00 PM'),
                                       ('16:00', '4:00 PM - 5:00 PM')
                                   ],
                                   validators=[DataRequired()],
                                   render_kw={'class': 'form-control', 'size': '7'})
    submit = SubmitField('Add Availability')
            
    def validate_specific_date(self, specific_date):
        if self.availability_type.data == 'specific' and (not specific_date.data or specific_date.data < date.today()):
            raise ValidationError('Please select a future date for specific availability.')
            
    def validate_day_of_week(self, day_of_week):
        if self.availability_type.data == 'recurring' and not day_of_week.data and day_of_week.data != 0:
            raise ValidationError('Please select a day of the week for recurring availability.')
    
    def validate_time_slots(self, time_slots):
        if not time_slots.data:
            raise ValidationError('Please select at least one time slot.')

class BookAppointmentForm(FlaskForm):
    appointment_date = DateField('Appointment Date', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = SelectField('Time Slot', validators=[DataRequired()], choices=[])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Book Appointment')
    
    def validate_appointment_date(self, appointment_date):
        if appointment_date.data < date.today():
            raise ValidationError('Appointment date cannot be in the past.')

class ComplaintForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Submit Complaint')

class PatientReportForm(FlaskForm):
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired(), Length(max=1000)])
    treatment_plan = TextAreaField('Treatment Plan', validators=[DataRequired(), Length(max=1000)])
    recommendations = TextAreaField('Recommendations', validators=[DataRequired(), Length(max=1000)])
    next_appointment = DateField('Next Appointment', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Generate Report')
    
    def validate_next_appointment(self, next_appointment):
        if next_appointment.data and next_appointment.data < date.today():
            raise ValidationError('Next appointment date cannot be in the past.')

class ChatMessageForm(FlaskForm):
    message_text = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=1000)], 
                                render_kw={'placeholder': 'Type your message here...', 'rows': 3})
    submit = SubmitField('Send')

class SliderImageForm(FlaskForm):
    title = StringField('Title', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    image_url = StringField('Image URL', validators=[DataRequired(), Length(max=255)])
    display_order = IntegerField('Display Order', validators=[DataRequired()])
    is_active = BooleanField('Is Active')
    submit = SubmitField('Add/Update Slider Image')
