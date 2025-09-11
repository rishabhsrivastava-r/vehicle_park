from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
db = SQLAlchemy() #this is the object imported in app.py

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    
    def set_password(self, password): #password checking k liye
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Admin(db.Model):
    __tablename__ = 'admins' #can be changed ny no of tmes..only used in db view
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)#pura parking lot ka logic
    prime_location_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    maximum_spots = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parking_spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')
    
    @property
    def available_spots(self):
        return sum(1 for spot in self.parking_spots if spot.status == 'A')
    
    @property
    def occupied_spots(self):
        return sum(1 for spot in self.parking_spots if spot.status == 'O')

class ParkingSpot(db.Model):#class table hota hai
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), default='A')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='spot', lazy=True)

class Reservation(db.Model):#foregn key prkinid h
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime)
    parking_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')
    
    def calculate_cost(self):
        if self.leaving_timestamp and self.parking_timestamp:
            duration = (self.leaving_timestamp - self.parking_timestamp).total_seconds() / 3600
            return round(duration * self.spot.lot.price_per_hour, 2)
        return 0

def create_default_admin():
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


def get_occupancy_summary(): #table bnane ke liye
    #Get simple occupancy statistics for charts
    total_spots = db.session.query(func.count(ParkingSpot.id)).scalar() or 0
    occupied_spots = db.session.query(func.count(ParkingSpot.id)).filter_by(status='O').scalar() or 0
    available_spots = total_spots - occupied_spots
    
    return {
        'occupied_spots': occupied_spots,
        'available_spots': available_spots,
        'total_spots': total_spots
    }

def get_lot_occupancy_summary():#table bnane k elliye
    #Get occupancy data for each parking lot
    lots_occupancy = []
    lots = ParkingLot.query.all()
    
    for lot in lots:
        lots_occupancy.append({
            'name': lot.prime_location_name,
            'occupied': lot.occupied_spots,
            'available': lot.available_spots,
            'total': lot.maximum_spots
        })
    
    return lots_occupancy