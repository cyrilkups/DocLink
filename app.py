from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///doctor_referral.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Add these configurations after app initialization
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Models
class Doctor(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    npi_id = db.Column(db.String(50), unique=True, nullable=False)
    state = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar_path = db.Column(db.String(200))
    connections = db.relationship('Connection', foreign_keys='Connection.doctor1_id', backref='doctor1', lazy=True)
    connections2 = db.relationship('Connection', foreign_keys='Connection.doctor2_id', backref='doctor2', lazy=True)
    sent_appointments = db.relationship('Appointment', foreign_keys='Appointment.sender_id', backref='sender', lazy=True)
    received_appointments = db.relationship('Appointment', foreign_keys='Appointment.receiver_id', backref='receiver', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor1_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    doctor2_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, cancelled
    priority = db.Column(db.String(20), default='normal')  # emergency, urgent, normal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Doctor.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('consultation'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"Current user authenticated: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        print("User already authenticated, redirecting to consultation")
        return redirect(url_for('consultation'))
    
    if request.method == 'POST':
        npi_id = request.form.get('npi_id')
        password = request.form.get('password')
        
        print(f"Login attempt with NPI ID: {npi_id}")
        print(f"Password provided: {bool(password)}")
        
        if not npi_id or not password:
            flash('Please provide both NPI ID and password', 'error')
            return render_template('login.html')
        
        try:
            doctor = Doctor.query.filter_by(npi_id=npi_id).first()
            if doctor:
                print(f"Found doctor: {doctor.full_name}")
                print(f"Stored password hash: {doctor.password_hash}")
                if doctor.check_password(password):
                    print("Password check passed, logging in user")
                    login_user(doctor, remember=True)
                    print(f"User logged in, authenticated status: {current_user.is_authenticated}")
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('consultation'))
                else:
                    print("Password check failed")
                    flash('Invalid password', 'error')
            else:
                print("No doctor found with that NPI ID")
                flash('No doctor found with that NPI ID', 'error')
        except Exception as e:
            print(f"Error during login: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('consultation'))
    
    if request.method == 'POST':
        # Check if NPI ID already exists
        if Doctor.query.filter_by(npi_id=request.form.get('npi_id')).first():
            flash('NPI ID already registered')
            return redirect(url_for('register'))
        
        # Check if email already exists
        if Doctor.query.filter_by(email=request.form.get('email')).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Check if passwords match
        if request.form.get('password') != request.form.get('confirm_password'):
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        # Create new doctor
        doctor = Doctor(
            full_name=request.form.get('full_name'),
            email=request.form.get('email'),
            specialization=request.form.get('specialization'),
            phone=request.form.get('phone'),
            npi_id=request.form.get('npi_id'),
            state=request.form.get('state'),
            address=request.form.get('address'),
            avatar_path=None  # Set default avatar path to None
        )
        doctor.set_password(request.form.get('password'))
        
        db.session.add(doctor)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    stats = {
        'total_consultations': 0,  # You can implement actual stats
        'total_patients': 0,
        'rating': 5.0
    }
    return render_template('profile.html', stats=stats)

@app.route('/consultation')
@login_required
def consultation():
    incoming = Appointment.query.filter_by(receiver_id=current_user.id).all()
    outgoing = Appointment.query.filter_by(sender_id=current_user.id).all()
    return render_template('consultation.html', incoming=incoming, outgoing=outgoing)

@app.route('/requests')
@login_required
def requests():
    # Get all doctors except current user
    doctors = Doctor.query.filter(Doctor.id != current_user.id).all()
    
    # Get existing connections
    connections = Connection.query.filter(
        ((Connection.doctor1_id == current_user.id) | (Connection.doctor2_id == current_user.id)) &
        (Connection.status == 'accepted')
    ).all()
    
    # Get pending requests
    pending_requests = Connection.query.filter(
        ((Connection.doctor1_id == current_user.id) | (Connection.doctor2_id == current_user.id)) &
        (Connection.status == 'pending')
    ).all()
    
    return render_template('requests.html', 
                         doctors=doctors, 
                         connections=connections,
                         pending_requests=pending_requests)

@app.route('/send_request/<int:doctor_id>', methods=['POST'])
@login_required
def send_request(doctor_id):
    # Check if request already exists
    existing = Connection.query.filter(
        ((Connection.doctor1_id == current_user.id) & (Connection.doctor2_id == doctor_id)) |
        ((Connection.doctor1_id == doctor_id) & (Connection.doctor2_id == current_user.id))
    ).first()
    
    if existing:
        flash('Request already exists')
        return redirect(url_for('requests'))
    
    connection = Connection(doctor1_id=current_user.id, doctor2_id=doctor_id)
    db.session.add(connection)
    db.session.commit()
    
    flash('Connection request sent')
    return redirect(url_for('requests'))

@app.route('/handle_request/<int:request_id>/<action>', methods=['POST'])
@login_required
def handle_request(request_id, action):
    connection = Connection.query.get_or_404(request_id)
    
    if connection.doctor2_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('requests'))
    
    if action == 'accept':
        connection.status = 'accepted'
    else:
        connection.status = 'rejected'
    
    db.session.commit()
    flash(f'Request {action}ed')
    return redirect(url_for('requests'))

@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        date_time = datetime.strptime(request.form.get('appointment_datetime'), '%Y-%m-%dT%H:%M')
        priority = request.form.get('priority', 'normal')
        
        if not doctor_id:
            flash('Please select a doctor', 'error')
            return redirect(url_for('book_appointment'))
        
        # Get the selected doctor
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash('Selected doctor not found', 'error')
            return redirect(url_for('book_appointment'))
        
        # Create the appointment
        appointment = Appointment(
            sender_id=current_user.id,
            receiver_id=doctor_id,
            date_time=date_time,
            status='pending',
            priority=priority
        )
        
        db.session.add(appointment)
        try:
            db.session.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('consultation'))
        except Exception as e:
            db.session.rollback()
            flash('Error booking appointment. Please try again.', 'error')
            return redirect(url_for('book_appointment'))
    
    # Get all doctors except current user
    available_doctors = Doctor.query.filter(Doctor.id != current_user.id).all()
    
    return render_template('book_appointment.html', doctors=available_doctors, now=datetime.now())

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.sender_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('consultation'))
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    flash('Appointment cancelled')
    return redirect(url_for('consultation'))

@app.route('/messages')
@login_required
def messages():
    # Get connected doctors for the chat list
    connections = Connection.query.filter(
        ((Connection.doctor1_id == current_user.id) | (Connection.doctor2_id == current_user.id)) &
        (Connection.status == 'accepted')
    ).all()
    
    connected_doctors = []
    for conn in connections:
        if conn.doctor1_id == current_user.id:
            doctor = Doctor.query.get(conn.doctor2_id)
        else:
            doctor = Doctor.query.get(conn.doctor1_id)
        connected_doctors.append(doctor)
    
    return render_template('messages.html', doctors=connected_doctors)

@app.route('/get_messages/<int:doctor_id>')
@login_required
def get_messages(doctor_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == doctor_id)) |
        ((Message.sender_id == doctor_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at).all()
    
    return jsonify([{
        'id': msg.id,
        'content': msg.content,
        'file_path': msg.file_path,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'is_sent': msg.sender_id == current_user.id
    } for msg in messages])

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    doctor_id = request.form.get('doctor_id')
    content = request.form.get('content')
    file = request.files.get('file')
    
    # Check if doctors are connected
    connection = Connection.query.filter(
        ((Connection.doctor1_id == current_user.id) | (Connection.doctor2_id == current_user.id)) &
        ((Connection.doctor1_id == doctor_id) | (Connection.doctor2_id == doctor_id)) &
        (Connection.status == 'accepted')
    ).first()
    
    if not connection:
        return jsonify({'error': 'Not connected with this doctor'}), 403
    
    file_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_path = url_for('static', filename=f'uploads/{filename}')
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=doctor_id,
        content=content,
        file_path=file_path
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'file_path': message.file_path,
        'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'is_sent': True
    })

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(f"{current_user.id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Delete old avatar if it exists
        if current_user.avatar_path:
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], current_user.avatar_path)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        
        # Save new avatar
        file.save(filepath)
        current_user.avatar_path = filename
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid file type'})

@app.route('/debug/users')
def debug_users():
    doctors = Doctor.query.all()
    return jsonify([{
        'id': d.id,
        'npi_id': d.npi_id,
        'full_name': d.full_name,
        'email': d.email
    } for d in doctors])

@app.route('/handle_appointment/<int:appointment_id>/<action>', methods=['POST'])
@login_required
def handle_appointment(appointment_id, action):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.receiver_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('consultation'))
    
    if action == 'accept':
        appointment.status = 'accepted'
        
        # Check if a connection already exists between the doctors
        existing_connection = Connection.query.filter(
            ((Connection.doctor1_id == appointment.sender_id) & (Connection.doctor2_id == appointment.receiver_id)) |
            ((Connection.doctor1_id == appointment.receiver_id) & (Connection.doctor2_id == appointment.sender_id))
        ).first()
        
        # If no connection exists, create one
        if not existing_connection:
            connection = Connection(
                doctor1_id=appointment.sender_id,
                doctor2_id=appointment.receiver_id,
                status='accepted'  # Automatically accept the connection
            )
            db.session.add(connection)
            flash('Appointment accepted and connection established', 'success')
        else:
            flash('Appointment accepted', 'success')
            
    elif action == 'reject':
        appointment.status = 'cancelled'
        flash('Appointment rejected', 'error')
    
    db.session.commit()
    return redirect(url_for('consultation'))

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create test doctors
        test_doctors = [
            {
                'full_name': 'Dr. John Smith',
                'email': 'john.smith@example.com',
                'specialization': 'Cardiology',
                'phone': '1234567890',
                'npi_id': 'NPI001',
                'state': 'CA',
                'address': '123 Medical Center Dr',
                'password': 'doctor123'
            },
            {
                'full_name': 'Dr. Sarah Johnson',
                'email': 'sarah.johnson@example.com',
                'specialization': 'Neurology',
                'phone': '2345678901',
                'npi_id': 'NPI002',
                'state': 'NY',
                'address': '456 Hospital Ave',
                'password': 'doctor123'
            },
            {
                'full_name': 'Dr. Michael Chen',
                'email': 'michael.chen@example.com',
                'specialization': 'Pediatrics',
                'phone': '3456789012',
                'npi_id': 'NPI003',
                'state': 'TX',
                'address': '789 Children\'s Way',
                'password': 'doctor123'
            },
            {
                'full_name': 'Dr. Emily Brown',
                'email': 'emily.brown@example.com',
                'specialization': 'Dermatology',
                'phone': '4567890123',
                'npi_id': 'NPI004',
                'state': 'FL',
                'address': '321 Skin Care Blvd',
                'password': 'doctor123'
            }
        ]
        
        print("\nCreating test doctors:")
        print("----------------------")
        for doctor_data in test_doctors:
            doctor = Doctor(
                full_name=doctor_data['full_name'],
                email=doctor_data['email'],
                specialization=doctor_data['specialization'],
                phone=doctor_data['phone'],
                npi_id=doctor_data['npi_id'],
                state=doctor_data['state'],
                address=doctor_data['address'],
                avatar_path=None
            )
            doctor.set_password(doctor_data['password'])
            db.session.add(doctor)
            print(f"Created doctor: {doctor_data['full_name']}")
            print(f"NPI ID: {doctor_data['npi_id']}")
            print(f"Password: {doctor_data['password']}")
            print("----------------------")
        
        try:
            db.session.commit()
            print("All test doctors created successfully!")
        except Exception as e:
            print(f"Error creating test doctors: {str(e)}")
            db.session.rollback()
    
    # Get port from environment variable for Render deployment
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True) 