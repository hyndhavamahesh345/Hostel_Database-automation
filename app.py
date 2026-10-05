import os
import sys
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Ensure backend directory is in python search path
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import Config
from db import db

# Locate frontend folder
ROOT_DIR = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) == 'backend' else CURRENT_DIR

template_dir = os.path.join(ROOT_DIR, 'frontend', 'templates')
if not os.path.exists(template_dir):
    template_dir = os.path.join(ROOT_DIR, 'templates')

static_dir = os.path.join(ROOT_DIR, 'frontend', 'static')
if not os.path.exists(static_dir):
    static_dir = os.path.join(ROOT_DIR, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config.from_object(Config)

# -------------------------------------------------------------
# Template Filters & Helpers
# -------------------------------------------------------------
@app.template_filter('currency')
def currency_filter(value):
    try:
        val = float(value or 0)
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{value}"

@app.template_filter('datetime_format')
def datetime_format_filter(value, fmt='%d %b %Y, %I:%M %p'):
    if not value:
        return '—'
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    try:
        dt = datetime.fromisoformat(str(value).replace(' ', 'T'))
        return dt.strftime(fmt)
    except Exception:
        return str(value)

@app.template_filter('date_format')
def date_format_filter(value, fmt='%d %b %Y'):
    if not value:
        return '—'
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    try:
        dt = datetime.fromisoformat(str(value).replace(' ', 'T'))
        return dt.strftime(fmt)
    except Exception:
        return str(value)

# Context processor for global template variables
@app.context_processor
def inject_global_data():
    return {
        'current_year': datetime.now().year,
        'current_user': session.get('username'),
        'user_role': session.get('role'),
        'student_id': session.get('student_id'),
        'db_engine': db.engine
    }

# -------------------------------------------------------------
# Authentication Decorators
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as administrator or warden.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') not in ['admin', 'warden']:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as a student.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'student':
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') in ['admin', 'warden']:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = db.fetch_one("SELECT * FROM Users WHERE username = %s", (username,))
        
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            if user['role'] == 'student':
                student = db.fetch_one("SELECT * FROM Student WHERE user_id = %s", (user['user_id'],))
                if student:
                    session['student_id'] = student['student_id']
                    session['student_name'] = student['name']
                    session['roll_number'] = student['roll_number']
                flash(f"Welcome back, {session.get('student_name', user['username'])}!", 'success')
                return redirect(url_for('student_dashboard'))
            else:
                session['admin_name'] = user['username'].capitalize()
                flash(f"Welcome, Administrator ({user['username']})!", 'success')
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    hostels = db.fetch_all("SELECT * FROM Hostel ORDER BY hostel_name")
    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip().upper()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        course = request.form.get('course', '').strip()
        year = request.form.get('year', '').strip()
        gender = request.form.get('gender', 'Female').strip()
        password = request.form.get('password', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        guardian_name = request.form.get('guardian_name', '').strip()
        address = request.form.get('address', '').strip()
        
        if not (roll_number and name and email and phone and password):
            flash('Please fill out all required fields.', 'danger')
            return render_template('register.html', hostels=hostels)
            
        existing_user = db.fetch_one("SELECT * FROM Users WHERE username = %s", (roll_number,))
        if existing_user:
            flash(f"Account with Roll Number '{roll_number}' already exists. Please log in.", 'warning')
            return redirect(url_for('login'))
            
        existing_email = db.fetch_one("SELECT * FROM Student WHERE email = %s", (email,))
        if existing_email:
            flash(f"Email '{email}' is already registered.", 'warning')
            return render_template('register.html', hostels=hostels)
            
        pwd_hash = generate_password_hash(password)
        try:
            user_id = db.execute_query("INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, 'student')", (roll_number, pwd_hash))
            db.execute_query("""
                INSERT INTO Student (user_id, roll_number, name, email, phone, course, year, gender, emergency_contact, guardian_name, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, roll_number, name, email, phone, course, year, gender, emergency_contact, guardian_name, address))
            
            flash('Registration successful! You can now log in with your Roll Number and Password.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error during registration: {e}", 'danger')
            
    return render_template('register.html', hostels=hostels)

# -------------------------------------------------------------
# Student Portal Routes
# -------------------------------------------------------------
@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student_id = session.get('student_id')
    student = db.fetch_one("SELECT * FROM Student WHERE student_id = %s", (student_id,))
    
    allocation = db.fetch_one("""
        SELECT ra.*, r.room_number, r.room_type, r.fee_per_semester, h.hostel_name, h.hostel_type, h.warden_name, h.contact_phone
        FROM Room_Allocation ra
        JOIN Room r ON ra.room_id = r.room_id
        JOIN Hostel h ON r.hostel_id = h.hostel_id
        WHERE ra.student_id = %s AND ra.status = 'Active'
    """, (student_id,))
    
    roommates = []
    if allocation:
        roommates = db.fetch_all("""
            SELECT s.name, s.roll_number, s.course, s.year, s.phone
            FROM Room_Allocation ra
            JOIN Student s ON ra.student_id = s.student_id
            WHERE ra.room_id = %s AND ra.status = 'Active' AND s.student_id != %s
        """, (allocation['room_id'], student_id))
    
    fees = db.fetch_all("SELECT * FROM Fee WHERE student_id = %s ORDER BY created_at DESC", (student_id,))
    total_fee = sum(f['amount'] for f in fees) if fees else 0
    total_paid = sum(f['amount_paid'] for f in fees) if fees else 0
    total_due = sum(f['due_amount'] for f in fees) if fees else 0
    
    complaints = db.fetch_all("SELECT * FROM Complaint WHERE student_id = %s ORDER BY complaint_date DESC LIMIT 5", (student_id,))
    leaves = db.fetch_all("SELECT * FROM Leave_Request WHERE student_id = %s ORDER BY applied_at DESC LIMIT 5", (student_id,))
    notices = db.fetch_all("SELECT * FROM Notice ORDER BY is_pinned DESC, date_posted DESC LIMIT 4")
    
    return render_template('student_dashboard.html',
                           student=student,
                           allocation=allocation,
                           roommates=roommates,
                           total_fee=total_fee,
                           total_paid=total_paid,
                           total_due=total_due,
                           complaints=complaints,
                           leaves=leaves,
                           notices=notices)

@app.route('/student/profile', methods=['GET', 'POST'])
@student_required
def student_profile():
    student_id = session.get('student_id')
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        guardian_name = request.form.get('guardian_name', '').strip()
        address = request.form.get('address', '').strip()
        new_password = request.form.get('new_password', '').strip()
        
        db.execute_query("""
            UPDATE Student 
            SET phone = %s, emergency_contact = %s, guardian_name = %s, address = %s
            WHERE student_id = %s
        """, (phone, emergency_contact, guardian_name, address, student_id))
        
        if new_password:
            user_id = session.get('user_id')
            pwd_hash = generate_password_hash(new_password)
            db.execute_query("UPDATE Users SET password_hash = %s WHERE user_id = %s", (pwd_hash, user_id))
            flash('Profile details and password updated successfully!', 'success')
        else:
            flash('Profile details updated successfully!', 'success')
            
        return redirect(url_for('student_profile'))
        
    student = db.fetch_one("SELECT * FROM Student WHERE student_id = %s", (student_id,))
    return render_template('profile.html', student=student)

@app.route('/student/room')
@student_required
def student_room():
    student_id = session.get('student_id')
    allocation = db.fetch_one("""
        SELECT ra.*, r.room_number, r.room_type, r.capacity, r.occupied, r.fee_per_semester,
               h.hostel_name, h.hostel_type, h.location, h.warden_name, h.contact_phone
        FROM Room_Allocation ra
        JOIN Room r ON ra.room_id = r.room_id
        JOIN Hostel h ON r.hostel_id = h.hostel_id
        WHERE ra.student_id = %s AND ra.status = 'Active'
    """, (student_id,))
    
    roommates = []
    if allocation:
        roommates = db.fetch_all("""
            SELECT s.name, s.roll_number, s.course, s.year, s.email, s.phone, ra.allocation_date
            FROM Room_Allocation ra
            JOIN Student s ON ra.student_id = s.student_id
            WHERE ra.room_id = %s AND ra.status = 'Active' AND s.student_id != %s
        """, (allocation['room_id'], student_id))
        
    return render_template('room.html', allocation=allocation, roommates=roommates)

@app.route('/student/fees', methods=['GET', 'POST'])
@student_required
def student_fees():
    student_id = session.get('student_id')
    
    if request.method == 'POST':
        fee_id = request.form.get('fee_id')
        pay_amount = float(request.form.get('amount', 0))
        txn_ref = request.form.get('txn_ref', f"TXN-ONLINE-{int(datetime.now().timestamp())}")
        
        fee = db.fetch_one("SELECT * FROM Fee WHERE fee_id = %s AND student_id = %s", (fee_id, student_id))
        if fee and pay_amount > 0:
            new_paid = min(fee['amount'], fee['amount_paid'] + pay_amount)
            new_status = 'Paid' if new_paid >= fee['amount'] else 'Partial'
            new_due = fee['amount'] - new_paid
            today = date.today().isoformat()
            
            db.execute_query("""
                UPDATE Fee 
                SET amount_paid = %s, due_amount = %s, status = %s, payment_date = %s, transaction_ref = %s, remarks = 'Online Student Payment'
                WHERE fee_id = %s
            """, (new_paid, new_due, new_status, today, txn_ref, fee_id))
            flash(f"Payment of ₹{pay_amount:,.2f} recorded successfully! Reference: {txn_ref}", 'success')
            return redirect(url_for('student_fees'))
            
    fees = db.fetch_all("SELECT * FROM Fee WHERE student_id = %s ORDER BY created_at DESC", (student_id,))
    total_fee = sum(f['amount'] for f in fees) if fees else 0
    total_paid = sum(f['amount_paid'] for f in fees) if fees else 0
    total_due = sum(f['due_amount'] for f in fees) if fees else 0
    
    return render_template('fees.html', fees=fees, total_fee=total_fee, total_paid=total_paid, total_due=total_due)

@app.route('/student/complaints', methods=['GET', 'POST'])
@student_required
def student_complaints():
    student_id = session.get('student_id')
    if request.method == 'POST':
        complaint_type = request.form.get('complaint_type', '').strip()
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium').strip()
        
        if not (complaint_type and title and description):
            flash('Please provide complaint category, title, and description.', 'danger')
        else:
            db.execute_query("""
                INSERT INTO Complaint (student_id, complaint_type, title, description, priority, status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')
            """, (student_id, complaint_type, title, description, priority))
            flash('Your complaint has been submitted successfully. The warden has been notified.', 'success')
            return redirect(url_for('student_complaints'))
            
    complaints = db.fetch_all("SELECT * FROM Complaint WHERE student_id = %s ORDER BY complaint_date DESC", (student_id,))
    return render_template('complaints.html', complaints=complaints)

@app.route('/student/leave', methods=['GET', 'POST'])
@student_required
def student_leave():
    student_id = session.get('student_id')
    if request.method == 'POST':
        leave_type = request.form.get('leave_type', 'Weekend Home').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        reason = request.form.get('reason', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        
        if not (start_date and end_date and reason):
            flash('Please enter start date, end date, and reason for leave.', 'danger')
        else:
            db.execute_query("""
                INSERT INTO Leave_Request (student_id, leave_type, start_date, end_date, reason, emergency_contact, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
            """, (student_id, leave_type, start_date, end_date, reason, emergency_contact))
            flash('Leave application submitted for warden approval!', 'success')
            return redirect(url_for('student_leave'))
            
    leaves = db.fetch_all("SELECT * FROM Leave_Request WHERE student_id = %s ORDER BY applied_at DESC", (student_id,))
    return render_template('leave.html', leaves=leaves)

@app.route('/student/notices')
@student_required
def student_notices():
    category = request.args.get('category')
    search = request.args.get('q', '').strip()
    
    query = "SELECT * FROM Notice WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = %s"
        params.append(category)
    if search:
        query += " AND (title LIKE %s OR description LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    query += " ORDER BY is_pinned DESC, date_posted DESC"
    notices = db.fetch_all(query, tuple(params))
    return render_template('notices.html', notices=notices, selected_category=category, search=search)

# -------------------------------------------------------------
# Warden / Admin Portal Routes
# -------------------------------------------------------------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_students = db.fetch_one("SELECT COUNT(*) AS count FROM Student")['count']
    total_rooms = db.fetch_one("SELECT COUNT(*) AS count FROM Room")['count']
    
    beds_data = db.fetch_one("SELECT SUM(capacity) AS total_beds, SUM(occupied) AS occupied_beds FROM Room")
    total_beds = beds_data['total_beds'] or 0
    occupied_beds = beds_data['occupied_beds'] or 0
    available_beds = max(0, total_beds - occupied_beds)
    
    pending_complaints = db.fetch_one("SELECT COUNT(*) AS count FROM Complaint WHERE status = 'Pending'")['count']
    pending_leaves = db.fetch_one("SELECT COUNT(*) AS count FROM Leave_Request WHERE status = 'Pending'")['count']
    
    fee_data = db.fetch_one("SELECT SUM(amount) AS total_fee, SUM(amount_paid) AS total_collected, SUM(due_amount) AS total_due FROM Fee")
    total_fee = fee_data['total_fee'] or 0
    total_collected = fee_data['total_collected'] or 0
    total_due = fee_data['total_due'] or 0
    
    recent_complaints = db.fetch_all("""
        SELECT c.*, s.name AS student_name, s.roll_number, r.room_number
        FROM Complaint c
        JOIN Student s ON c.student_id = s.student_id
        LEFT JOIN Room_Allocation ra ON s.student_id = ra.student_id AND ra.status = 'Active'
        LEFT JOIN Room r ON ra.room_id = r.room_id
        ORDER BY c.complaint_date DESC LIMIT 5
    """)
    
    recent_leaves = db.fetch_all("""
        SELECT lr.*, s.name AS student_name, s.roll_number, s.phone
        FROM Leave_Request lr
        JOIN Student s ON lr.student_id = s.student_id
        WHERE lr.status = 'Pending'
        ORDER BY lr.applied_at DESC LIMIT 5
    """)
    
    hostels_summary = db.fetch_all("""
        SELECT h.hostel_id, h.hostel_name, h.hostel_type,
               COUNT(r.room_id) AS room_count,
               SUM(r.capacity) AS capacity,
               SUM(r.occupied) AS occupied
        FROM Hostel h
        LEFT JOIN Room r ON h.hostel_id = r.hostel_id
        GROUP BY h.hostel_id
    """)
    
    notices = db.fetch_all("SELECT * FROM Notice ORDER BY is_pinned DESC, date_posted DESC LIMIT 4")
    
    return render_template('admin_dashboard.html',
                           total_students=total_students,
                           total_rooms=total_rooms,
                           total_beds=total_beds,
                           occupied_beds=occupied_beds,
                           available_beds=available_beds,
                           pending_complaints=pending_complaints,
                           pending_leaves=pending_leaves,
                           total_fee=total_fee,
                           total_collected=total_collected,
                           total_due=total_due,
                           recent_complaints=recent_complaints,
                           recent_leaves=recent_leaves,
                           hostels_summary=hostels_summary,
                           notices=notices)

# Student Management CRUD
@app.route('/admin/students', methods=['GET', 'POST'])
@admin_required
def admin_students():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            roll_number = request.form.get('roll_number', '').strip().upper()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            course = request.form.get('course', '').strip()
            year = request.form.get('year', '').strip()
            gender = request.form.get('gender', 'Female').strip()
            password = request.form.get('password', 'student123').strip()
            emergency_contact = request.form.get('emergency_contact', '').strip()
            guardian_name = request.form.get('guardian_name', '').strip()
            address = request.form.get('address', '').strip()
            allocate_room_id = request.form.get('room_id')
            
            if db.fetch_one("SELECT * FROM Student WHERE roll_number = %s OR email = %s", (roll_number, email)):
                flash('Student with this Roll Number or Email already exists.', 'danger')
                return redirect(url_for('admin_students'))
                
            pwd_hash = generate_password_hash(password)
            user_id = db.execute_query("INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, 'student')", (roll_number, pwd_hash))
            student_id = db.execute_query("""
                INSERT INTO Student (user_id, roll_number, name, email, phone, course, year, gender, emergency_contact, guardian_name, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, roll_number, name, email, phone, course, year, gender, emergency_contact, guardian_name, address))
            
            fee_amount = 35000.00
            if allocate_room_id:
                room = db.fetch_one("SELECT * FROM Room WHERE room_id = %s", (allocate_room_id,))
                if room and room['occupied'] < room['capacity']:
                    fee_amount = float(room['fee_per_semester'])
                    db.execute_query("""
                        INSERT INTO Room_Allocation (student_id, room_id, allocation_date, status, remarks)
                        VALUES (%s, %s, %s, 'Active', 'Allocated upon student registration')
                    """, (student_id, allocate_room_id, date.today().isoformat()))
                    db.update_room_occupancy(allocate_room_id)
            
            db.execute_query("""
                INSERT INTO Fee (student_id, academic_term, amount, amount_paid, due_amount, status, remarks)
                VALUES (%s, 'Fall Semester 2026', %s, 0.00, %s, 'Pending', 'Initial Semester Hostel Fee')
            """, (student_id, fee_amount, fee_amount))
            
            flash(f"Student '{name}' ({roll_number}) added successfully!", 'success')
            return redirect(url_for('admin_students'))
            
        elif action == 'edit':
            student_id = request.form.get('student_id')
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            course = request.form.get('course', '').strip()
            year = request.form.get('year', '').strip()
            gender = request.form.get('gender', '').strip()
            emergency_contact = request.form.get('emergency_contact', '').strip()
            guardian_name = request.form.get('guardian_name', '').strip()
            address = request.form.get('address', '').strip()
            
            db.execute_query("""
                UPDATE Student 
                SET name = %s, email = %s, phone = %s, course = %s, year = %s, gender = %s,
                    emergency_contact = %s, guardian_name = %s, address = %s
                WHERE student_id = %s
            """, (name, email, phone, course, year, gender, emergency_contact, guardian_name, address, student_id))
            flash('Student information updated successfully!', 'success')
            return redirect(url_for('admin_students'))
            
        elif action == 'delete':
            student_id = request.form.get('student_id')
            student = db.fetch_one("SELECT * FROM Student WHERE student_id = %s", (student_id,))
            if student:
                alloc = db.fetch_one("SELECT room_id FROM Room_Allocation WHERE student_id = %s AND status = 'Active'", (student_id,))
                if alloc:
                    room_id = alloc['room_id']
                    db.execute_query("DELETE FROM Room_Allocation WHERE student_id = %s", (student_id,))
                    db.update_room_occupancy(room_id)
                    
                if student['user_id']:
                    db.execute_query("DELETE FROM Users WHERE user_id = %s", (student['user_id'],))
                db.execute_query("DELETE FROM Student WHERE student_id = %s", (student_id,))
                flash(f"Student record for '{student['name']}' removed.", 'info')
            return redirect(url_for('admin_students'))
            
    search = request.args.get('q', '').strip()
    gender_filter = request.args.get('gender', '')
    course_filter = request.args.get('course', '')
    
    query = """
        SELECT s.*, r.room_number, r.room_type, h.hostel_name, ra.allocation_id,
               COALESCE((SELECT status FROM Fee WHERE student_id = s.student_id ORDER BY fee_id DESC LIMIT 1), 'No Record') AS fee_status,
               COALESCE((SELECT due_amount FROM Fee WHERE student_id = s.student_id ORDER BY fee_id DESC LIMIT 1), 0.0) AS fee_due
        FROM Student s
        LEFT JOIN Room_Allocation ra ON s.student_id = ra.student_id AND ra.status = 'Active'
        LEFT JOIN Room r ON ra.room_id = r.room_id
        LEFT JOIN Hostel h ON r.hostel_id = h.hostel_id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (s.name LIKE %s OR s.roll_number LIKE %s OR s.email LIKE %s OR r.room_number LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
    if gender_filter:
        query += " AND s.gender = %s"
        params.append(gender_filter)
    if course_filter:
        query += " AND s.course LIKE %s"
        params.append(f"%{course_filter}%")
        
    query += " ORDER BY s.student_id DESC"
    students = db.fetch_all(query, tuple(params))
    
    available_rooms = db.fetch_all("""
        SELECT r.*, h.hostel_name 
        FROM Room r 
        JOIN Hostel h ON r.hostel_id = h.hostel_id 
        WHERE r.occupied < r.capacity
        ORDER BY h.hostel_name, r.room_number
    """)
    hostels = db.fetch_all("SELECT * FROM Hostel ORDER BY hostel_name")
    
    return render_template('students.html',
                           students=students,
                           available_rooms=available_rooms,
                           hostels=hostels,
                           search=search,
                           gender_filter=gender_filter,
                           course_filter=course_filter)

# Room Management
@app.route('/admin/rooms', methods=['GET', 'POST'])
@admin_required
def admin_rooms():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_room':
            hostel_id = request.form.get('hostel_id')
            room_number = request.form.get('room_number', '').strip().upper()
            room_type = request.form.get('room_type')
            capacity = int(request.form.get('capacity', 2))
            fee_per_semester = float(request.form.get('fee_per_semester', 35000.0))
            
            existing = db.fetch_one("SELECT * FROM Room WHERE hostel_id = %s AND room_number = %s", (hostel_id, room_number))
            if existing:
                flash(f"Room '{room_number}' already exists in this hostel block.", 'danger')
            else:
                db.execute_query("""
                    INSERT INTO Room (hostel_id, room_number, room_type, capacity, occupied, fee_per_semester, status)
                    VALUES (%s, %s, %s, %s, 0, %s, 'Available')
                """, (hostel_id, room_number, room_type, capacity, fee_per_semester))
                flash(f"Room {room_number} added successfully!", 'success')
            return redirect(url_for('admin_rooms'))
            
        elif action == 'edit_room':
            room_id = request.form.get('room_id')
            room_type = request.form.get('room_type')
            capacity = int(request.form.get('capacity', 2))
            fee_per_semester = float(request.form.get('fee_per_semester', 35000.0))
            status = request.form.get('status', 'Available')
            
            db.execute_query("""
                UPDATE Room 
                SET room_type = %s, capacity = %s, fee_per_semester = %s, status = %s
                WHERE room_id = %s
            """, (room_type, capacity, fee_per_semester, status, room_id))
            db.update_room_occupancy(room_id)
            flash('Room updated successfully!', 'success')
            return redirect(url_for('admin_rooms'))
            
        elif action == 'add_hostel':
            hostel_name = request.form.get('hostel_name', '').strip()
            hostel_type = request.form.get('hostel_type', 'Girls')
            location = request.form.get('location', 'Woxsen Campus, Hyderabad')
            warden_name = request.form.get('warden_name', 'Hostel Warden')
            contact_phone = request.form.get('contact_phone', '')
            
            db.execute_query("""
                INSERT INTO Hostel (hostel_name, hostel_type, location, warden_name, contact_phone)
                VALUES (%s, %s, %s, %s, %s)
            """, (hostel_name, hostel_type, location, warden_name, contact_phone))
            flash(f"Hostel block '{hostel_name}' created successfully!", 'success')
            return redirect(url_for('admin_rooms'))

    hostel_id_filter = request.args.get('hostel_id', '')
    status_filter = request.args.get('status', '')
    
    query = """
        SELECT r.*, h.hostel_name, h.hostel_type,
               (r.capacity - r.occupied) AS available_beds
        FROM Room r
        JOIN Hostel h ON r.hostel_id = h.hostel_id
        WHERE 1=1
    """
    params = []
    if hostel_id_filter:
        query += " AND r.hostel_id = %s"
        params.append(hostel_id_filter)
    if status_filter:
        query += " AND r.status = %s"
        params.append(status_filter)
        
    query += " ORDER BY h.hostel_name, r.room_number"
    rooms = db.fetch_all(query, tuple(params))
    
    for room in rooms:
        room['occupants'] = db.fetch_all("""
            SELECT s.name, s.roll_number, s.course, s.phone 
            FROM Room_Allocation ra
            JOIN Student s ON ra.student_id = s.student_id
            WHERE ra.room_id = %s AND ra.status = 'Active'
        """, (room['room_id'],))
        
    hostels = db.fetch_all("SELECT * FROM Hostel ORDER BY hostel_name")
    return render_template('rooms.html', rooms=rooms, hostels=hostels, selected_hostel=hostel_id_filter, selected_status=status_filter)

# Room Allocation Management
@app.route('/admin/allocations', methods=['GET', 'POST'])
@admin_required
def admin_allocations():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'allocate':
            student_id = request.form.get('student_id')
            room_id = request.form.get('room_id')
            remarks = request.form.get('remarks', 'Allocated by Woxsen Warden')
            
            existing = db.fetch_one("SELECT * FROM Room_Allocation WHERE student_id = %s AND status = 'Active'", (student_id,))
            if existing:
                flash('This student already has an active room allocation. Please vacate or transfer first.', 'warning')
                return redirect(url_for('admin_allocations'))
                
            room = db.fetch_one("SELECT * FROM Room WHERE room_id = %s", (room_id,))
            if not room or room['occupied'] >= room['capacity']:
                flash('Selected room is full or unavailable.', 'danger')
                return redirect(url_for('admin_allocations'))
                
            db.execute_query("""
                INSERT INTO Room_Allocation (student_id, room_id, allocation_date, status, remarks)
                VALUES (%s, %s, %s, 'Active', %s)
            """, (student_id, room_id, date.today().isoformat(), remarks))
            db.update_room_occupancy(room_id)
            flash('Student allocated to room successfully!', 'success')
            return redirect(url_for('admin_allocations'))
            
        elif action == 'vacate':
            allocation_id = request.form.get('allocation_id')
            alloc = db.fetch_one("SELECT * FROM Room_Allocation WHERE allocation_id = %s", (allocation_id,))
            if alloc:
                db.execute_query("UPDATE Room_Allocation SET status = 'Vacated' WHERE allocation_id = %s", (allocation_id,))
                db.update_room_occupancy(alloc['room_id'])
                flash('Room allocation marked as Vacated.', 'info')
            return redirect(url_for('admin_allocations'))
            
        elif action == 'transfer':
            allocation_id = request.form.get('allocation_id')
            new_room_id = request.form.get('new_room_id')
            
            alloc = db.fetch_one("SELECT * FROM Room_Allocation WHERE allocation_id = %s", (allocation_id,))
            new_room = db.fetch_one("SELECT * FROM Room WHERE room_id = %s", (new_room_id,))
            
            if alloc and new_room:
                if new_room['occupied'] >= new_room['capacity']:
                    flash('Target transfer room is already full.', 'danger')
                    return redirect(url_for('admin_allocations'))
                    
                old_room_id = alloc['room_id']
                db.execute_query("UPDATE Room_Allocation SET status = 'Transferred' WHERE allocation_id = %s", (allocation_id,))
                db.update_room_occupancy(old_room_id)
                db.execute_query("""
                    INSERT INTO Room_Allocation (student_id, room_id, allocation_date, status, remarks)
                    VALUES (%s, %s, %s, 'Active', 'Transferred by Warden')
                """, (alloc['student_id'], new_room_id, date.today().isoformat()))
                db.update_room_occupancy(new_room_id)
                flash('Student successfully transferred to new room!', 'success')
            return redirect(url_for('admin_allocations'))
            
    allocations = db.fetch_all("""
        SELECT ra.*, s.name AS student_name, s.roll_number, s.course, s.year, s.gender, s.phone,
               r.room_number, r.room_type, r.fee_per_semester, h.hostel_name
        FROM Room_Allocation ra
        JOIN Student s ON ra.student_id = s.student_id
        JOIN Room r ON ra.room_id = r.room_id
        JOIN Hostel h ON r.hostel_id = h.hostel_id
        ORDER BY ra.status ASC, ra.allocation_date DESC
    """)
    
    unallocated_students = db.fetch_all("""
        SELECT s.* FROM Student s
        WHERE s.student_id NOT IN (
            SELECT student_id FROM Room_Allocation WHERE status = 'Active'
        )
        ORDER BY s.name
    """)
    
    available_rooms = db.fetch_all("""
        SELECT r.*, h.hostel_name, (r.capacity - r.occupied) AS available_beds
        FROM Room r 
        JOIN Hostel h ON r.hostel_id = h.hostel_id 
        WHERE r.occupied < r.capacity
        ORDER BY h.hostel_name, r.room_number
    """)
    
    return render_template('admin_allocations.html',
                           allocations=allocations,
                           unallocated_students=unallocated_students,
                           available_rooms=available_rooms)

# Fee Management
@app.route('/admin/fees', methods=['GET', 'POST'])
@admin_required
def admin_fees():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'record_payment':
            fee_id = request.form.get('fee_id')
            pay_amount = float(request.form.get('amount_paid', 0))
            txn_ref = request.form.get('transaction_ref', f"TXN-OFFLINE-{int(datetime.now().timestamp())}")
            remarks = request.form.get('remarks', 'Offline cash/counter payment')
            
            fee = db.fetch_one("SELECT * FROM Fee WHERE fee_id = %s", (fee_id,))
            if fee:
                new_paid = min(fee['amount'], fee['amount_paid'] + pay_amount)
                new_status = 'Paid' if new_paid >= fee['amount'] else 'Partial'
                new_due = fee['amount'] - new_paid
                today = date.today().isoformat()
                
                db.execute_query("""
                    UPDATE Fee 
                    SET amount_paid = %s, due_amount = %s, status = %s, payment_date = %s, transaction_ref = %s, remarks = %s
                    WHERE fee_id = %s
                """, (new_paid, new_due, new_status, today, txn_ref, remarks, fee_id))
                flash(f"Payment of ₹{pay_amount:,.2f} recorded for Fee Record #{fee_id}.", 'success')
            return redirect(url_for('admin_fees'))
            
        elif action == 'create_fee':
            student_id = request.form.get('student_id')
            academic_term = request.form.get('academic_term', 'Fall Semester 2026')
            amount = float(request.form.get('amount', 35000.0))
            remarks = request.form.get('remarks', 'Semester hostel fee invoice')
            
            db.execute_query("""
                INSERT INTO Fee (student_id, academic_term, amount, amount_paid, due_amount, status, remarks)
                VALUES (%s, %s, %s, 0.00, %s, 'Pending', %s)
            """, (student_id, academic_term, amount, amount, remarks))
            flash('Fee invoice created successfully!', 'success')
            return redirect(url_for('admin_fees'))

    status_filter = request.args.get('status')
    search = request.args.get('q', '').strip()
    
    query = """
        SELECT f.*, s.name AS student_name, s.roll_number, s.course, s.phone,
               r.room_number, h.hostel_name
        FROM Fee f
        JOIN Student s ON f.student_id = s.student_id
        LEFT JOIN Room_Allocation ra ON s.student_id = ra.student_id AND ra.status = 'Active'
        LEFT JOIN Room r ON ra.room_id = r.room_id
        LEFT JOIN Hostel h ON r.hostel_id = h.hostel_id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND f.status = %s"
        params.append(status_filter)
    if search:
        query += " AND (s.name LIKE %s OR s.roll_number LIKE %s OR f.transaction_ref LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
    query += " ORDER BY f.status ASC, f.created_at DESC"
    fees = db.fetch_all(query, tuple(params))
    
    summary = db.fetch_one("SELECT SUM(amount) AS total, SUM(amount_paid) AS collected, SUM(due_amount) AS due FROM Fee")
    students = db.fetch_all("SELECT student_id, name, roll_number FROM Student ORDER BY name")
    
    return render_template('admin_fees.html',
                           fees=fees,
                           summary=summary,
                           students=students,
                           status_filter=status_filter,
                           search=search)

# Complaint Management
@app.route('/admin/complaints', methods=['GET', 'POST'])
@admin_required
def admin_complaints():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_status':
            complaint_id = request.form.get('complaint_id')
            status = request.form.get('status')
            resolution_notes = request.form.get('resolution_notes', '').strip()
            
            resolved_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'Resolved' else None
            
            db.execute_query("""
                UPDATE Complaint 
                SET status = %s, resolution_notes = %s, resolved_at = %s
                WHERE complaint_id = %s
            """, (status, resolution_notes, resolved_at, complaint_id))
            flash(f"Complaint #{complaint_id} updated to '{status}'.", 'success')
            return redirect(url_for('admin_complaints'))

    status_filter = request.args.get('status')
    type_filter = request.args.get('type')
    
    query = """
        SELECT c.*, s.name AS student_name, s.roll_number, s.phone,
               r.room_number, h.hostel_name
        FROM Complaint c
        JOIN Student s ON c.student_id = s.student_id
        LEFT JOIN Room_Allocation ra ON s.student_id = ra.student_id AND ra.status = 'Active'
        LEFT JOIN Room r ON ra.room_id = r.room_id
        LEFT JOIN Hostel h ON r.hostel_id = h.hostel_id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND c.status = %s"
        params.append(status_filter)
    if type_filter:
        query += " AND c.complaint_type = %s"
        params.append(type_filter)
        
    query += " ORDER BY CASE c.status WHEN 'Pending' THEN 1 WHEN 'In Progress' THEN 2 ELSE 3 END, c.complaint_date DESC"
    complaints = db.fetch_all(query, tuple(params))
    
    return render_template('admin_complaints.html',
                           complaints=complaints,
                           status_filter=status_filter,
                           type_filter=type_filter)

# Leave Management
@app.route('/admin/leave', methods=['GET', 'POST'])
@admin_required
def admin_leave():
    if request.method == 'POST':
        action = request.form.get('action')
        leave_id = request.form.get('leave_id')
        admin_remarks = request.form.get('admin_remarks', '').strip()
        
        if action == 'approve':
            db.execute_query("""
                UPDATE Leave_Request 
                SET status = 'Approved', admin_remarks = %s 
                WHERE leave_id = %s
            """, (admin_remarks or 'Approved by Warden', leave_id))
            flash(f"Leave Request #{leave_id} Approved.", 'success')
            
        elif action == 'reject':
            db.execute_query("""
                UPDATE Leave_Request 
                SET status = 'Rejected', admin_remarks = %s 
                WHERE leave_id = %s
            """, (admin_remarks or 'Rejected by Warden due to institutional regulations', leave_id))
            flash(f"Leave Request #{leave_id} Rejected.", 'warning')
            
        return redirect(url_for('admin_leave'))

    status_filter = request.args.get('status')
    query = """
        SELECT lr.*, s.name AS student_name, s.roll_number, s.course, s.year, s.phone,
               r.room_number, h.hostel_name
        FROM Leave_Request lr
        JOIN Student s ON lr.student_id = s.student_id
        LEFT JOIN Room_Allocation ra ON s.student_id = ra.student_id AND ra.status = 'Active'
        LEFT JOIN Room r ON ra.room_id = r.room_id
        LEFT JOIN Hostel h ON r.hostel_id = h.hostel_id
        WHERE 1=1
    """
    params = []
    if status_filter:
        query += " AND lr.status = %s"
        params.append(status_filter)
        
    query += " ORDER BY CASE lr.status WHEN 'Pending' THEN 1 ELSE 2 END, lr.applied_at DESC"
    leaves = db.fetch_all(query, tuple(params))
    
    return render_template('admin_leave.html', leaves=leaves, status_filter=status_filter)

# Notice Management
@app.route('/admin/notices', methods=['GET', 'POST'])
@admin_required
def admin_notices():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            title = request.form.get('title', '').strip()
            category = request.form.get('category', 'General')
            description = request.form.get('description', '').strip()
            posted_by = request.form.get('posted_by', 'Woxsen Hostel Administration')
            is_pinned = 1 if request.form.get('is_pinned') else 0
            
            db.execute_query("""
                INSERT INTO Notice (title, category, description, posted_by, is_pinned)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, category, description, posted_by, is_pinned))
            flash('Notice published to all students!', 'success')
            return redirect(url_for('admin_notices'))
            
        elif action == 'delete':
            notice_id = request.form.get('notice_id')
            db.execute_query("DELETE FROM Notice WHERE notice_id = %s", (notice_id,))
            flash('Notice deleted.', 'info')
            return redirect(url_for('admin_notices'))
            
        elif action == 'toggle_pin':
            notice_id = request.form.get('notice_id')
            notice = db.fetch_one("SELECT is_pinned FROM Notice WHERE notice_id = %s", (notice_id,))
            if notice:
                new_pin = 0 if notice['is_pinned'] else 1
                db.execute_query("UPDATE Notice SET is_pinned = %s WHERE notice_id = %s", (new_pin, notice_id))
                flash('Notice pin status updated.', 'info')
            return redirect(url_for('admin_notices'))

    notices = db.fetch_all("SELECT * FROM Notice ORDER BY is_pinned DESC, date_posted DESC")
    return render_template('admin_notices.html', notices=notices)

# Reports & Analytical View
@app.route('/admin/reports')
@admin_required
def admin_reports():
    hostel_occupancy = db.fetch_all("""
        SELECT h.hostel_name, h.hostel_type,
               COUNT(r.room_id) AS total_rooms,
               SUM(r.capacity) AS total_capacity,
               SUM(r.occupied) AS total_occupied,
               (SUM(r.capacity) - SUM(r.occupied)) AS vacant_beds
        FROM Hostel h
        LEFT JOIN Room r ON h.hostel_id = r.hostel_id
        GROUP BY h.hostel_id
    """)
    
    fee_breakdown = db.fetch_all("""
        SELECT status, COUNT(*) AS record_count, SUM(amount) AS total_billed, SUM(amount_paid) AS total_paid, SUM(due_amount) AS total_due
        FROM Fee
        GROUP BY status
    """)
    
    defaulters = db.fetch_all("""
        SELECT s.name, s.roll_number, s.phone, s.email, f.amount, f.amount_paid, f.due_amount, f.academic_term
        FROM Fee f
        JOIN Student s ON f.student_id = s.student_id
        WHERE f.status IN ('Pending', 'Partial') AND f.due_amount > 0
        ORDER BY f.due_amount DESC
    """)
    
    complaint_stats = db.fetch_all("""
        SELECT complaint_type, COUNT(*) AS count,
               SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_count,
               SUM(CASE WHEN status != 'Resolved' THEN 1 ELSE 0 END) AS open_count
        FROM Complaint
        GROUP BY complaint_type
    """)
    
    student_distribution = db.fetch_all("""
        SELECT course, year, COUNT(*) AS count
        FROM Student
        GROUP BY course, year
        ORDER BY course, year
    """)
    
    return render_template('reports.html',
                           hostel_occupancy=hostel_occupancy,
                           fee_breakdown=fee_breakdown,
                           defaulters=defaulters,
                           complaint_stats=complaint_stats,
                           student_distribution=student_distribution)

# Database Settings & MySQL Live Connector Hub
@app.route('/admin/db-settings', methods=['GET', 'POST'])
@admin_required
def admin_db_settings():
    test_result = None
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'test_mysql':
            host = request.form.get('db_host', 'localhost')
            port = int(request.form.get('db_port', 3306))
            user = request.form.get('db_user', 'root')
            password = request.form.get('db_password', '')
            dbname = request.form.get('db_name', 'hostel_management')
            
            try:
                import pymysql
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    cursorclass=pymysql.cursors.DictCursor,
                    connect_timeout=3
                )
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4;")
                conn.close()
                test_result = {
                    'success': True,
                    'message': f"Successfully connected to MySQL server on {host}:{port} and verified database `{dbname}`!"
                }
                
                Config.DB_HOST = host
                Config.DB_PORT = port
                Config.DB_USER = user
                Config.DB_PASSWORD = password
                Config.DB_NAME = dbname
                
                db._detect_and_init_engine()
                flash('MySQL credentials verified and connected successfully!', 'success')
            except Exception as e:
                test_result = {
                    'success': False,
                    'message': f"Failed to connect to MySQL: {e}"
                }
                flash(f"Connection test failed: {e}", 'danger')
                
        elif action == 'switch_sqlite':
            db.engine = 'sqlite'
            db._init_sqlite_schema()
            flash('Switched active database engine to SQLite (Built-in zero-setup storage).', 'info')
            
    table_counts = {
        'Users': db.fetch_one("SELECT COUNT(*) AS c FROM Users")['c'],
        'Hostel': db.fetch_one("SELECT COUNT(*) AS c FROM Hostel")['c'],
        'Room': db.fetch_one("SELECT COUNT(*) AS c FROM Room")['c'],
        'Student': db.fetch_one("SELECT COUNT(*) AS c FROM Student")['c'],
        'Room_Allocation': db.fetch_one("SELECT COUNT(*) AS c FROM Room_Allocation")['c'],
        'Fee': db.fetch_one("SELECT COUNT(*) AS c FROM Fee")['c'],
        'Complaint': db.fetch_one("SELECT COUNT(*) AS c FROM Complaint")['c'],
        'Leave_Request': db.fetch_one("SELECT COUNT(*) AS c FROM Leave_Request")['c'],
        'Notice': db.fetch_one("SELECT COUNT(*) AS c FROM Notice")['c'],
    }
    
    return render_template('db_settings.html',
                           config=Config,
                           active_engine=db.engine,
                           mysql_error=db.mysql_error,
                           table_counts=table_counts,
                           test_result=test_result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
