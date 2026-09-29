# Vehicle Parking Management System
                          
## Introduction
A Flask-based web application for efficient parking management with real-time occupancy tracking, automated billing, and data visualization for both administrators and users.

## Tech Stack
**Backend**: Flask, SQLAlchemy, SQLite  
**Frontend**: Bootstrap 5.1.3, Chart.js, Jinja2  
**Security**: Werkzeug password hashing

## Features
- **Admin**: Dashboard analytics, parking lot CRUD, user management
- **User**: Real-time booking, reservation management, parking history
- **System**: Responsive design, secure authentication, data visualization

## Quick Setup
git clone <repository-url>
cd vehicle-parking-app
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
pip install -r requirements.txt
python app.py
## Access
- **Live Demo**: [Vehicle Parking Management System](https://vehicle-park-2.onrender.com/)
- **URL**: http://localhost:5000
- **Admin**: username `admin`, password `admin123`
- **User**: Register new account
## Database
5 tables: User, Admin, ParkingLot, ParkingSpot, Reservation with proper relationships and constraints.
## Architecture
MVC pattern with Flask blueprints, template inheritance, and modular design for scalability.
