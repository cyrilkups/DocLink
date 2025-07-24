Access project here: https://doclink1.onrender.com

# Doctor Referral System

A web application that helps doctors refer their patients to one another by connecting, scheduling consultations, and securely sharing messages and documents.

## Features

- Doctor registration and authentication using NIER ID
- Doctor-to-doctor connection requests
- Appointment scheduling between connected doctors
- Secure messaging system with file sharing
- Consultation history tracking
- Profile management

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd doctor-referral-system
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python app.py
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

### Registration
1. Click on "Register" to create a new account
2. Fill in all required information including:
   - Full Name
   - Email
   - Specialization
   - Phone Number
   - NIER ID (unique License ID)
   - State
   - Address
   - Password

### Login
1. Use your NIER ID and password to log in
2. You will be redirected to the consultation page after successful login

### Connecting with Other Doctors
1. Navigate to the "Requests" page
2. Browse available doctors
3. Send connection requests to doctors you want to connect with
4. Accept or reject incoming connection requests

### Booking Appointments
1. Navigate to "Book Appointment" in the left sidebar
2. Select a connected doctor
3. Choose date and time
4. Submit the appointment request

### Messaging
1. Navigate to the "Messages" page
2. Select a connected doctor from the list
3. Send text messages or share files
4. View message history

### Viewing Consultations
1. Navigate to the "Consultation" page
2. View incoming and outgoing consultations
3. Cancel appointments if needed

## Security Features

- Password hashing
- Secure file uploads
- Session management
- Input validation
- Access control for connected doctors only

## File Structure

```
doctor-referral-system/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/            # Static files
│   ├── css/
│   │   └── style.css  # Custom styles
│   └── uploads/       # Uploaded files
└── templates/         # HTML templates
    ├── base.html      # Base template
    ├── login.html     # Login page
    ├── register.html  # Registration page
    ├── profile.html   # Profile page
    ├── consultation.html  # Consultation page
    ├── requests.html  # Connection requests page
    ├── book_appointment.html  # Appointment booking page
    └── messages.html  # Messaging page
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
