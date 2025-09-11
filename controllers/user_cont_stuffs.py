from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.dtabse_define_stuffs import db, User, ParkingLot, ParkingSpot, Reservation,get_occupancy_summary 
from datetime import datetime
from sqlalchemy import func

user_bllp = Blueprint('user', __name__)

@user_bllp.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        uname = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        pwd = request.form['password']
        #email and password check kreega
        if User.query.filter_by(username=uname).first():
            flash('Username already exists!', 'error')
            return render_template('user_register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('user_register.html')
        
        n_user = User(username=uname, email=email, phone=phone)
        n_user.set_password(pwd)#n_user is new user
        
        db.session.add(n_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('user.user_login'))
    
    return render_template('user_register.html')

@user_bllp.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):#login verify
            session['user_id'] = user.id
            session['user_type'] = 'user'
            flash('Login is successful!', 'success')
            return redirect(url_for('user.user_dashboard'))
        else:
            flash('Invalid username or password!', 'error')#error red color
    
    return render_template('user_login.html')

@user_bllp.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('user.user_login'))
    
    user = User.query.get(session['user_id'])
    occupancy_summary = get_occupancy_summary()

    lots = ParkingLot.query.all() #dashboard mein same user id se active and oplete visible
    active_reservations = Reservation.query.filter_by(user_id=user.id, status='active').all()
    completed_reservations = Reservation.query.filter_by(user_id=user.id, status='completed').all()
    
    return render_template('user_dashboard.html',
                    occupancy_summary=occupancy_summary,
                user=user, lots=lots,
                active_reservations=active_reservations,
            completed_reservations=completed_reservations)

@user_bllp.route('/book_spot/<int:lot_id>', methods=['POST'])
def book_spot(lot_id):#use for booking spot
    if 'user_id' not in session:
        return redirect(url_for('user.user_login'))
    
    vehicle_number = request.form['vehicle_number']
    already_parked = Reservation.query.filter_by(vehicle_number=vehicle_number, status='active').first()
    if already_parked:
        flash('This vehicle is already parked. Please release it first before booking another spot.')
        return redirect(url_for('user_dashboard'))

    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    
    if not spot:
        flash('No available spots in this parking lot! Try later', 'error')
        return redirect(url_for('user.user_dashboard'))
    
    reservation = Reservation(
        spot_id=spot.id,
        user_id=session['user_id'],
        vehicle_number=vehicle_number
    )
    
    spot.status = 'O'
    
    db.session.add(reservation)
    db.session.commit()
    
    flash('Parking spot booked successfully!', 'success')
    return redirect(url_for('user.user_dashboard'))

@user_bllp.route('/release_spot/<int:reservation_id>')
def release_spot(reservation_id):
    if 'user_id' not in session:#checking user
        return redirect(url_for('user.user_login'))
    
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.user_id != session['user_id']:
        flash('Unauthorized access!', 'error')
        return redirect(url_for('user.user_dashboard'))
    
    reservation.leaving_timestamp = datetime.utcnow()
    reservation.parking_cost = reservation.calculate_cost()#defined in model yeh function
    reservation.status = 'completed'
    
    spot = ParkingSpot.query.get(reservation.spot_id)
    spot.status = 'A' #spot ko o se hta dga 
    
    db.session.commit()
    
    flash(f'Parking spot released! Total cost: ₹{reservation.parking_cost}', 'success')
    return redirect(url_for('user.user_dashboard'))

