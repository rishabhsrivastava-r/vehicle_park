#picks data from model and throw in template..middlemen
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.dtabse_define_stuffs import db, Admin, ParkingLot, ParkingSpot, Reservation, User ,get_occupancy_summary, get_lot_occupancy_summary
from datetime import datetime
from sqlalchemy import func

admin_blp = Blueprint('admin', __name__) #used for managing all the routes of a admin specific func..we defined only a single line in app.py else we would have to dit seprately

@admin_blp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['user_type'] = 'admin'
            flash('Login Done!', 'success')
            return redirect('/admin/dashboard')
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('admin_login.html')

@admin_blp.route('/dashboard')
def admin_dashboard(): #used for the dashboard admmin kka
    if 'admin_id' not in session: #check krna for admin hai ya nhi
        return redirect(url_for('admin.admin_login'))
    

    occupancy_summary = get_occupancy_summary()
    lots_occupancy = get_lot_occupancy_summary()
    lots = ParkingLot.query.all()
    users = User.query.all()
    total_spots = len(ParkingSpot.query.all())
    occupied_spots = len(ParkingSpot.query.filter_by(status='O').all())

    available_spots = total_spots - occupied_spots

    recent_reservations = (
        db.session.query(Reservation)
        .outerjoin(ParkingSpot)
        .outerjoin(ParkingLot)
        .outerjoin(User)
        .filter(Reservation.status == 'active')
        .all()
    )
    
    return render_template(
        'admin_dashboard.html',
        occupancy_summary=occupancy_summary,
        lots_occupancy=lots_occupancy,
        lots=lots,
        users=users,
        total_spots=total_spots,
        occupied_spots=occupied_spots,
        available_spots=available_spots,
        recent_reservations=recent_reservations
    )

@admin_blp.route('/create_lot', methods=['GET', 'POST'])
def create_lot():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    
    if request.method == 'POST':
        lot = ParkingLot(
            prime_location_name=request.form['location_name'],
            address=request.form['address'],
            pincode=request.form['pincode'],
            price_per_hour=float(request.form['price_per_hour']),
            maximum_spots=int(request.form['maximum_spots'])
        ) #lot mein sb kuch jaayega
        
        db.session.add(lot)
        db.session.flush()
        
        max_spots = int(request.form['maximum_spots'])
        for i in range(max_spots):
            spot = ParkingSpot(lot_id=lot.id, spot_number= i + 1)
            db.session.add(spot)

        
        db.session.commit()
        flash('Parking lot created successfully!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('create_lot.html')

@admin_blp.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id): #used for editing  the lot in db
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'POST':
        lot.prime_location_name = request.form['location_name']
        lot.address = request.form['address']
        lot.pincode = request.form['pincode']
        lot.price_per_hour = float(request.form['price_per_hour'])
        
        new_max_spots = int(request.form['maximum_spots'])
        current_spots = len(lot.parking_spots)
        
        if new_max_spots > current_spots:
            for i in range(current_spots + 1, new_max_spots + 1):
                spot = ParkingSpot(lot_id=lot.id, spot_number=i)
                db.session.add(spot)
        elif new_max_spots < current_spots:
    # Count spots that can be safely deleted (no reservations)
            deletable_spots = []
            for spot in ParkingSpot.query.filter_by(lot_id=lot.id, status='A').order_by(ParkingSpot.spot_number.desc()).all():
                if not Reservation.query.filter_by(spot_id=spot.id).first():
                 deletable_spots.append(spot)
    
            spots_to_delete = min(len(deletable_spots), current_spots - new_max_spots)
    
            if spots_to_delete < (current_spots - new_max_spots):
                flash('Cannot reduce spots that much - some spots have reservation history.', 'error')
                return render_template('edit_lot.html', lot=lot)
    
    # Delete the safe spots
            for spot in deletable_spots[:spots_to_delete]:
                db.session.delete(spot)
        
        lot.maximum_spots = new_max_spots
        db.session.commit() #change commit hua
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    return render_template('edit_lot.html', lot=lot)


@admin_blp.route('/view_lot/<int:lot_id>')
def view_lot(lot_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    
    active_reservations = {}
    reservations = db.session.query(Reservation).join(ParkingSpot).filter(
        ParkingSpot.lot_id == lot_id, Reservation.status == 'active'
    ).all()
    
    for reservation in reservations:#looping in each reservtn
        active_reservations[reservation.spot_id] = reservation
    
    context = {
    'lot': lot,
    'spots': spots,
    'active_reservations': active_reservations
    }
    return render_template('view_lot.html', **context) #isme dict alg se bnayi fir pass kiya..bahut complex ho rha tha


@admin_blp.route('/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    
    # FIXED: Check for active reservations first
    active_reservations = db.session.query(Reservation).join(ParkingSpot).filter(
        ParkingSpot.lot_id == lot_id,
        Reservation.status == 'active'
    ).count()
    
    if active_reservations > 0:
        flash(f'Cannot delete parking lot with {active_reservations} active reservations!', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    # FIXED: Check for ANY reservations (including completed ones)
    any_reservations = db.session.query(Reservation).join(ParkingSpot).filter(
        ParkingSpot.lot_id == lot_id
    ).count()
    
    if any_reservations > 0:
        flash('Cannot delete parking lot that has reservation history.', 'error')#cosnider markin inactive will implement later
        return redirect(url_for('admin.admin_dashboard'))
    
    # Safe to delete bcz no reservations exist
    try:
        # Delete parking spots first (which should have no reservations)
        ParkingSpot.query.filter_by(lot_id=lot_id).delete()
        
        # Then delete the lot 
        db.session.delete(lot)
        db.session.commit()
        
        flash('Parking lot deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting parking lot. Please try again.', 'error')
    
    return redirect(url_for('admin.admin_dashboard'))
#need to implement inactive active feature


