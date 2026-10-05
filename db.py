import os
import sqlite3
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

class Database:
    def __init__(self):
        self.engine = 'sqlite'
        self.mysql_error = None
        self._detect_and_init_engine()

    def _detect_and_init_engine(self):
        """Attempts to connect to MySQL if configured, otherwise falls back to SQLite."""
        if Config.DB_ENGINE in ['mysql', 'auto']:
            try:
                conn = pymysql.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    cursorclass=pymysql.cursors.DictCursor,
                    connect_timeout=3
                )
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4;")
                conn.select_db(Config.DB_NAME)
                self.engine = 'mysql'
                self.mysql_error = None
                conn.close()
                self._init_mysql_schema()
                print(f"[DB] Connected successfully to MySQL Database: `{Config.DB_NAME}` on {Config.DB_HOST}:{Config.DB_PORT}")
                return
            except Exception as e:
                self.mysql_error = str(e)
                print(f"[DB Notice] MySQL connection not established ({e}). Using local SQLite engine ({Config.SQLITE_DB_PATH}) for seamless zero-setup operation.")
        
        self.engine = 'sqlite'
        self._init_sqlite_schema()
        print(f"[DB] Active Engine: SQLite (Database: {Config.SQLITE_DB_PATH})")

    def get_connection(self):
        """Returns a database connection based on active engine."""
        if self.engine == 'mysql':
            return pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        else:
            conn = sqlite3.connect(Config.SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

    def _normalize_sql(self, query: str) -> str:
        """Adapts parameter placeholders between MySQL (%s) and SQLite (?)."""
        if self.engine == 'sqlite':
            return query.replace('%s', '?')
        return query

    def fetch_all(self, query, params=None):
        """Fetches all rows matching the query as a list of dicts."""
        norm_query = self._normalize_sql(query)
        conn = self.get_connection()
        try:
            if self.engine == 'mysql':
                with conn.cursor() as cursor:
                    cursor.execute(norm_query, params or ())
                    return cursor.fetchall()
            else:
                cursor = conn.cursor()
                cursor.execute(norm_query, params or ())
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            conn.close()

    def fetch_one(self, query, params=None):
        """Fetches a single row matching the query as a dict."""
        norm_query = self._normalize_sql(query)
        conn = self.get_connection()
        try:
            if self.engine == 'mysql':
                with conn.cursor() as cursor:
                    cursor.execute(norm_query, params or ())
                    return cursor.fetchone()
            else:
                cursor = conn.cursor()
                cursor.execute(norm_query, params or ())
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def execute_query(self, query, params=None):
        """Executes INSERT, UPDATE, DELETE queries and returns lastrowid or affected rows."""
        norm_query = self._normalize_sql(query)
        conn = self.get_connection()
        try:
            if self.engine == 'mysql':
                with conn.cursor() as cursor:
                    cursor.execute(norm_query, params or ())
                    last_id = cursor.lastrowid
                    return last_id or cursor.rowcount
            else:
                cursor = conn.cursor()
                cursor.execute(norm_query, params or ())
                conn.commit()
                last_id = cursor.lastrowid
                return last_id or cursor.rowcount
        finally:
            conn.close()

    def _init_sqlite_schema(self):
        """Initializes SQLite tables and seeds Woxsen University data."""
        conn = sqlite3.connect(Config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Hostel (
            hostel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostel_name TEXT NOT NULL UNIQUE,
            hostel_type TEXT NOT NULL DEFAULT 'Girls',
            location TEXT DEFAULT 'Woxsen University Campus, Hyderabad',
            warden_name TEXT DEFAULT 'Dr. Sunita Rao',
            contact_phone TEXT DEFAULT '+91 9845012345',
            total_rooms INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS Student (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            roll_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            gender TEXT NOT NULL DEFAULT 'Female',
            emergency_contact TEXT,
            guardian_name TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Room (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostel_id INTEGER NOT NULL,
            room_number TEXT NOT NULL,
            room_type TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 2,
            occupied INTEGER NOT NULL DEFAULT 0,
            fee_per_semester REAL NOT NULL DEFAULT 35000.00,
            status TEXT NOT NULL DEFAULT 'Available',
            UNIQUE (hostel_id, room_number),
            FOREIGN KEY (hostel_id) REFERENCES Hostel(hostel_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Room_Allocation (
            allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            allocation_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            remarks TEXT DEFAULT 'Allocated by Woxsen Warden',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES Room(room_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Fee (
            fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            academic_term TEXT NOT NULL DEFAULT 'Fall Semester 2026',
            amount REAL NOT NULL,
            amount_paid REAL NOT NULL DEFAULT 0.00,
            due_amount REAL NOT NULL DEFAULT 0.00,
            payment_date DATE,
            status TEXT NOT NULL DEFAULT 'Pending',
            transaction_ref TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Complaint (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            complaint_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium',
            complaint_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'Pending',
            resolution_notes TEXT,
            resolved_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Leave_Request (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL DEFAULT 'Weekend Home',
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT NOT NULL,
            emergency_contact TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            admin_remarks TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Notice (
            notice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            description TEXT NOT NULL,
            date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            posted_by TEXT DEFAULT 'Woxsen Hostel Administration',
            is_pinned INTEGER DEFAULT 0
        );
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM Users")
        if cursor.fetchone()[0] == 0:
            self.reseed_woxsen_data(conn)
        
        conn.close()

    def _init_mysql_schema(self):
        """Initializes MySQL tables and seeds Woxsen University data if empty."""
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'Users'")
                if not cursor.fetchone():
                    sql_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.sql')
                    if os.path.exists(sql_file_path):
                        with open(sql_file_path, 'r', encoding='utf-8') as f:
                            statements = f.read().split(';')
                            for stmt in statements:
                                stmt = stmt.strip()
                                if stmt:
                                    try:
                                        cursor.execute(stmt)
                                    except Exception as err:
                                        pass
                
                cursor.execute("SELECT COUNT(*) AS c FROM Users")
                row = cursor.fetchone()
                if not row or row['c'] == 0:
                    self.reseed_woxsen_data(conn)
        except Exception as e:
            print(f"[DB] Error executing MySQL schema: {e}")
        finally:
            conn.close()

    def reseed_woxsen_data(self, conn=None):
        """Seeds or reseeds the database with Woxsen University data and all female student records."""
        need_close = False
        if conn is None:
            conn = self.get_connection()
            need_close = True

        cursor = conn.cursor()
        
        if self.engine == 'sqlite':
            cursor.execute("PRAGMA foreign_keys = OFF")
            
        # Clear existing tables for fresh Woxsen seed in proper dependency order
        cursor.execute("DELETE FROM Notice")
        cursor.execute("DELETE FROM Leave_Request")
        cursor.execute("DELETE FROM Complaint")
        cursor.execute("DELETE FROM Fee")
        cursor.execute("DELETE FROM Room_Allocation")
        cursor.execute("DELETE FROM Student")
        cursor.execute("DELETE FROM Room")
        cursor.execute("DELETE FROM Hostel")
        cursor.execute("DELETE FROM Users")
        
        if self.engine == 'sqlite':
            cursor.execute("DELETE FROM sqlite_sequence")

        pwd_admin = generate_password_hash('admin123')
        pwd_warden = generate_password_hash('warden123')
        pwd_student = generate_password_hash('student123')

        users = [
            ('admin', pwd_admin, 'admin'),
            ('warden', pwd_warden, 'warden'),
            ('WU202601', pwd_student, 'student'),
            ('WU202602', pwd_student, 'student'),
            ('WU202603', pwd_student, 'student'),
            ('WU202604', pwd_student, 'student'),
            ('WU202605', pwd_student, 'student'),
            ('WU202606', pwd_student, 'student')
        ]
        param_placeholder = "%s, %s, %s" if self.engine == 'mysql' else "?, ?, ?"
        cursor.executemany(f"INSERT INTO Users (username, password_hash, role) VALUES ({param_placeholder})", users)

        hostels = [
            ('Woxsen Amber Girls Hostel (Block A)', 'Girls', 'Woxsen South Campus, Hyderabad', 'Dr. Sunita Rao', '+91 9845012345', 30),
            ('Woxsen Coral Girls Hostel (Block B)', 'Girls', 'Woxsen South Campus, Hyderabad', 'Prof. Priya Nair', '+91 9845023456', 25),
            ('Woxsen Ruby Girls Hostel (Block C)', 'Girls', 'Woxsen Central Campus, Hyderabad', 'Dr. Meenakshi Sharma', '+91 9845034567', 35),
            ('Woxsen Emerald Girls Hostel (Block D)', 'Girls', 'Woxsen East Campus, Hyderabad', 'Mrs. Lakshmi Prasad', '+91 9845045678', 30)
        ]
        param_h = "%s, %s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Hostel (hostel_name, hostel_type, location, warden_name, contact_phone, total_rooms) VALUES ({param_h})", hostels)

        rooms = [
            (1, 'A-101', 'Double AC', 2, 2, 45000.0, 'Full'),
            (1, 'A-102', 'Double AC', 2, 2, 45000.0, 'Full'),
            (1, 'A-103', 'Single AC', 1, 1, 60000.0, 'Full'),
            (1, 'A-104', 'Double Non-AC', 2, 1, 35000.0, 'Available'),
            (2, 'B-201', 'Double AC', 2, 1, 45000.0, 'Available'),
            (2, 'B-202', 'Single AC', 1, 0, 60000.0, 'Available'),
            (3, 'C-101', 'Double AC', 2, 0, 45000.0, 'Available'),
            (3, 'C-102', 'Single AC', 1, 0, 60000.0, 'Available'),
            (4, 'D-101', 'Double AC', 2, 0, 45000.0, 'Available')
        ]
        param_r = "%s, %s, %s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Room (hostel_id, room_number, room_type, capacity, occupied, fee_per_semester, status) VALUES ({param_r})", rooms)

        # All Girls Names - Woxsen University
        students = [
            (3, 'WU202601', 'Sruthika Reddy', 'sruthika.reddy@woxsen.edu.in', '+91 9876543201', 'B.Tech Computer Science & AI', '3rd Year', 'Female', '+91 9811122201', 'Venkat Reddy', 'Plot 45, Jubilee Hills, Hyderabad'),
            (4, 'WU202602', 'Ananya Deshmukh', 'ananya.deshmukh@woxsen.edu.in', '+91 9876543202', 'B.Tech Computer Science', '3rd Year', 'Female', '+91 9811122202', 'Mahesh Deshmukh', '78 Shivajinagar, Pune'),
            (5, 'WU202603', 'Kavya Sharma', 'kavya.sharma@woxsen.edu.in', '+91 9876543203', 'B.Tech Data Science', '2nd Year', 'Female', '+91 9811122203', 'Rajeev Sharma', 'Flat 304, Palm Meadows, Bengaluru'),
            (6, 'WU202604', 'Sneha Patel', 'sneha.patel@woxsen.edu.in', '+91 9876543204', 'BBA Business Analytics', '2nd Year', 'Female', '+91 9811122204', 'Kishore Patel', 'B-14 Vastrapur, Ahmedabad'),
            (7, 'WU202605', 'Riya Sen', 'riya.sen@woxsen.edu.in', '+91 9876543205', 'B.Des Fashion & Product Design', '1st Year', 'Female', '+91 9811122205', 'Subhash Sen', 'Salt Lake Sector V, Kolkata'),
            (8, 'WU202606', 'Pooja Verma', 'pooja.verma@woxsen.edu.in', '+91 9876543206', 'MBA General Management', '1st Year', 'Female', '+91 9811122206', 'Anil Verma', 'House 12, Civil Lines, Jaipur')
        ]
        param_s = "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Student (user_id, roll_number, name, email, phone, course, year, gender, emergency_contact, guardian_name, address) VALUES ({param_s})", students)

        allocations = [
            (1, 1, '2026-08-01', 'Active', 'Allocated for Academic Year 2026-27'),
            (2, 1, '2026-08-01', 'Active', 'Allocated for Academic Year 2026-27'),
            (3, 2, '2026-08-05', 'Active', 'Allocated for Academic Year 2026-27'),
            (4, 2, '2026-08-05', 'Active', 'Allocated for Academic Year 2026-27'),
            (5, 3, '2026-08-10', 'Active', 'Allocated for Academic Year 2026-27'),
            (6, 5, '2026-08-12', 'Active', 'Allocated for Academic Year 2026-27')
        ]
        param_a = "%s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Room_Allocation (student_id, room_id, allocation_date, status, remarks) VALUES ({param_a})", allocations)

        fees = [
            (1, 'Fall Semester 2026', 45000.0, 45000.0, 0.0, '2026-08-02', 'Paid', 'TXN-WOXSEN-90812', 'Full semester fee paid via Woxsen Portal NetBanking'),
            (2, 'Fall Semester 2026', 45000.0, 25000.0, 20000.0, '2026-08-15', 'Partial', 'TXN-WOXSEN-90845', 'First installment received'),
            (3, 'Fall Semester 2026', 45000.0, 45000.0, 0.0, '2026-08-06', 'Paid', 'TXN-WOXSEN-90901', 'Paid via UPI Transfer'),
            (4, 'Fall Semester 2026', 45000.0, 45000.0, 0.0, '2026-08-08', 'Paid', 'TXN-WOXSEN-90915', 'Full payment verified'),
            (5, 'Fall Semester 2026', 60000.0, 30000.0, 30000.0, '2026-08-11', 'Partial', 'TXN-WOXSEN-90940', 'Single Room first installment'),
            (6, 'Fall Semester 2026', 45000.0, 0.0, 45000.0, None, 'Pending', None, 'Pending payment reminder sent')
        ]
        param_f = "%s, %s, %s, %s, %s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Fee (student_id, academic_term, amount, amount_paid, due_amount, payment_date, status, transaction_ref, remarks) VALUES ({param_f})", fees)

        complaints = [
            (1, 'Wi-Fi', 'High-Speed Wi-Fi connectivity in Amber Block A', 'Signal fluctuates during evening online coding and study sessions on 1st floor corridor.', 'Medium', '2026-10-01 14:30:00', 'In Progress', 'Woxsen IT Infrastructure team assigned to calibrate access point.', None),
            (2, 'Water', 'Solar hot water temperature adjustment', 'Morning water supply in bathroom A-101 is slightly lukewarm.', 'Low', '2026-09-28 09:15:00', 'Resolved', 'Facility plumbing team calibrated the thermostat solar valve.', '2026-09-30 16:00:00'),
            (3, 'Cleanliness', 'Common study lounge sanitization', 'Block A ground floor study area deep cleaning requested.', 'High', '2026-10-03 10:00:00', 'Pending', None, None),
            (4, 'Electricity', 'Ceiling fan regulator replacement', 'Fan regulator knob is loose in Room A-102.', 'Medium', '2026-10-04 18:20:00', 'In Progress', 'Campus electrician scheduled for maintenance.', None),
            (5, 'Fan/AC', 'Air Conditioner filter cleaning in Single Room A-103', 'AC cooling air flow is gentle and needs regular mesh cleaning.', 'Low', '2026-10-05 11:00:00', 'Pending', None, None)
        ]
        param_c = "%s, %s, %s, %s, %s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Complaint (student_id, complaint_type, title, description, priority, complaint_date, status, resolution_notes, resolved_at) VALUES ({param_c})", complaints)

        leaves = [
            (1, 'Weekend Home', '2026-10-10', '2026-10-13', 'Visiting family in Jubilee Hills for weekend.', '+91 981112201', 'Approved', 'Approved by Warden. Return to campus by 8:30 PM Sunday.'),
            (2, 'Medical', '2026-10-06', '2026-10-08', 'Health checkup and medical consultation.', '+91 981112202', 'Approved', 'Medical prescription verified by campus clinic.'),
            (3, 'Academic/Event', '2026-10-15', '2026-10-18', 'Representing Woxsen University in National Hackathon.', '+91 981112203', 'Pending', None),
            (4, 'Weekend Home', '2026-10-20', '2026-10-23', 'Attending family function in hometown.', '+91 981112204', 'Pending', None)
        ]
        param_l = "%s, %s, %s, %s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Leave_Request (student_id, leave_type, start_date, end_date, reason, emergency_contact, status, admin_remarks) VALUES ({param_l})", leaves)

        notices = [
            ('Woxsen University Hostel Curfew & Campus Shuttle Timings', 'General', 'Reminder: Woxsen South Campus hostel entry gates close strictly at 9:30 PM. The internal electric campus shuttles operate until 10:00 PM for library users.', '2026-10-02 09:00:00', 'Office of the Chief Warden', 1),
            ('Fall Semester Hostel & Mess Fee Settlement Deadline', 'Fee Deadline', 'All students with pending hostel fee dues for Fall Semester 2026 are requested to complete settlement on the Woxsen Portal before October 15.', '2026-10-03 11:30:00', 'Woxsen Accounts & Hostel Admin', 1),
            ('Annual Woxsen Sports & Cultural Fest Accommodation Guidelines', 'Events', 'Guest accommodation and inter-university tournament schedules for badminton, basketball, and indoor games are available at the student sports desk.', '2026-10-04 15:00:00', 'Woxsen Student Council', 0),
            ('Solar Water Tank Sanitization Notice', 'Maintenance', 'Scheduled maintenance and sanitization for Amber and Coral blocks overhead solar tanks this Saturday between 10 AM to 1 PM.', '2026-09-25 08:30:00', 'Campus Facilities Team', 0)
        ]
        param_n = "%s, %s, %s, %s, %s, %s" if self.engine == 'mysql' else "?, ?, ?, ?, ?, ?"
        cursor.executemany(f"INSERT INTO Notice (title, category, description, date_posted, posted_by, is_pinned) VALUES ({param_n})", notices)
        
        conn.commit()
        if self.engine == 'sqlite':
            cursor.execute("PRAGMA foreign_keys = ON")
        if need_close:
            conn.close()
        print("[DB] Database successfully populated with Woxsen University seed data and all female student records!")

    def update_room_occupancy(self, room_id):
        """Recalculates occupancy and status for a given room."""
        row = self.fetch_one("SELECT COUNT(*) AS active_count FROM Room_Allocation WHERE room_id = %s AND status = 'Active'", (room_id,))
        count = row['active_count'] if row else 0
        
        room = self.fetch_one("SELECT capacity FROM Room WHERE room_id = %s", (room_id,))
        if room:
            capacity = room['capacity']
            status = 'Full' if count >= capacity else 'Available'
            self.execute_query("UPDATE Room SET occupied = %s, status = %s WHERE room_id = %s", (count, status, room_id))

# Global DB Instance
db = Database()
