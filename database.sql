-- ====================================================================
-- WOXSEN UNIVERSITY - HOSTEL ACCOMMODATION & STUDENT SERVICES (DBMS)
-- Database Name: hostel_management
-- Supported: MySQL 8.0+ / MySQL Workbench / MariaDB
-- ====================================================================

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS hostel_management;
USE hostel_management;

-- Disable foreign key checks during initialization
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------
-- 2. Drop existing tables safely
-- -----------------------------------------------------
DROP TABLE IF EXISTS Notice;
DROP TABLE IF EXISTS Leave_Request;
DROP TABLE IF EXISTS Complaint;
DROP TABLE IF EXISTS Fee;
DROP TABLE IF EXISTS Room_Allocation;
DROP TABLE IF EXISTS Room;
DROP TABLE IF EXISTS Student;
DROP TABLE IF EXISTS Hostel;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Visitor;
DROP TABLE IF EXISTS visitor;

-- -----------------------------------------------------
-- 3. Table: Users (For secure authentication & role management)
-- -----------------------------------------------------
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(60) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'warden', 'student') NOT NULL DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 4. Table: Hostel (Stores Woxsen University hostel blocks)
-- -----------------------------------------------------
CREATE TABLE Hostel (
    hostel_id INT AUTO_INCREMENT PRIMARY KEY,
    hostel_name VARCHAR(100) NOT NULL UNIQUE,
    hostel_type ENUM('Girls', 'Boys', 'Co-Ed') NOT NULL DEFAULT 'Girls',
    location VARCHAR(150) DEFAULT 'Woxsen University Campus, Hyderabad',
    warden_name VARCHAR(100) DEFAULT 'Dr. Sunita Rao',
    contact_phone VARCHAR(20) DEFAULT '+91 9845012345',
    total_rooms INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 5. Table: Student (Stores female student profiles)
-- -----------------------------------------------------
CREATE TABLE Student (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    roll_number VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    course VARCHAR(60) NOT NULL,
    year VARCHAR(20) NOT NULL,
    gender ENUM('Female', 'Male', 'Other') NOT NULL DEFAULT 'Female',
    emergency_contact VARCHAR(20),
    guardian_name VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 6. Table: Room (Stores room details and capacity)
-- -----------------------------------------------------
CREATE TABLE Room (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    hostel_id INT NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    room_type ENUM('Single AC', 'Single Non-AC', 'Double AC', 'Double Non-AC', 'Triple Non-AC') NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    occupied INT NOT NULL DEFAULT 0,
    fee_per_semester DECIMAL(10, 2) NOT NULL DEFAULT 35000.00,
    status ENUM('Available', 'Full', 'Under Maintenance') NOT NULL DEFAULT 'Available',
    UNIQUE KEY unique_hostel_room (hostel_id, room_number),
    FOREIGN KEY (hostel_id) REFERENCES Hostel(hostel_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 7. Table: Room_Allocation (Manages student room assignments)
-- -----------------------------------------------------
CREATE TABLE Room_Allocation (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    room_id INT NOT NULL,
    allocation_date DATE NOT NULL,
    status ENUM('Active', 'Vacated', 'Transferred') NOT NULL DEFAULT 'Active',
    remarks VARCHAR(255) DEFAULT 'Allocated by Woxsen Warden',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES Room(room_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 8. Table: Fee (Stores student fee records and status)
-- -----------------------------------------------------
CREATE TABLE Fee (
    fee_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    academic_term VARCHAR(50) NOT NULL DEFAULT 'Fall Semester 2026',
    amount DECIMAL(10, 2) NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    due_amount DECIMAL(10, 2) GENERATED ALWAYS AS (amount - amount_paid) STORED,
    payment_date DATE,
    status ENUM('Paid', 'Pending', 'Partial') NOT NULL DEFAULT 'Pending',
    transaction_ref VARCHAR(100),
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 9. Table: Complaint (Stores student complaints and resolution)
-- -----------------------------------------------------
CREATE TABLE Complaint (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    complaint_type ENUM('Water', 'Electricity', 'Fan/AC', 'Wi-Fi', 'Cleanliness', 'Maintenance', 'Other') NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    priority ENUM('Low', 'Medium', 'High', 'Emergency') NOT NULL DEFAULT 'Medium',
    complaint_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'In Progress', 'Resolved') NOT NULL DEFAULT 'Pending',
    resolution_notes TEXT,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 10. Table: Leave_Request (Stores student leave applications)
-- -----------------------------------------------------
CREATE TABLE Leave_Request (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    leave_type ENUM('Weekend Home', 'Medical', 'Academic/Event', 'Emergency', 'Other') NOT NULL DEFAULT 'Weekend Home',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT NOT NULL,
    emergency_contact VARCHAR(20),
    status ENUM('Pending', 'Approved', 'Rejected') NOT NULL DEFAULT 'Pending',
    admin_remarks VARCHAR(255),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 11. Table: Notice (Stores Woxsen hostel notices and announcements)
-- -----------------------------------------------------
CREATE TABLE Notice (
    notice_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    category ENUM('General', 'Maintenance', 'Fee Deadline', 'Events', 'Urgent') NOT NULL DEFAULT 'General',
    description TEXT NOT NULL,
    date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_by VARCHAR(100) DEFAULT 'Woxsen Hostel Administration',
    is_pinned BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- 12. DBMS Views (Demonstrating View abstraction)
-- -----------------------------------------------------
CREATE OR REPLACE VIEW View_Student_Allocations AS
SELECT 
    s.student_id,
    s.roll_number,
    s.name AS student_name,
    s.email,
    s.phone,
    s.gender,
    s.course,
    s.year,
    h.hostel_name,
    h.hostel_type,
    r.room_number,
    r.room_type,
    r.fee_per_semester,
    ra.allocation_id,
    ra.allocation_date,
    ra.status AS allocation_status
FROM Student s
LEFT JOIN Room_Allocation ra ON s.student_id = ra.student_id AND ra.status = 'Active'
LEFT JOIN Room r ON ra.room_id = r.room_id
LEFT JOIN Hostel h ON r.hostel_id = h.hostel_id;

CREATE OR REPLACE VIEW View_Room_Occupancy AS
SELECT 
    h.hostel_name,
    r.room_id,
    r.room_number,
    r.room_type,
    r.capacity,
    r.occupied,
    (r.capacity - r.occupied) AS available_beds,
    r.status,
    r.fee_per_semester
FROM Room r
JOIN Hostel h ON r.hostel_id = h.hostel_id;

-- -----------------------------------------------------
-- 13. Seed Initial Demo Data (Woxsen University - All Girls Names)
-- -----------------------------------------------------
INSERT INTO Users (user_id, username, password_hash, role) VALUES 
(1, 'admin', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'admin'),
(2, 'warden', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'warden'),
(3, 'WU202601', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'student'),
(4, 'WU202602', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'student'),
(5, 'WU202603', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'student'),
(6, 'WU202604', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'student'),
(7, 'WU202605', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'student'),
(8, 'WU202606', 'scrypt:32768:8:1$u7a99L5wK4L2$f7db6ec126786ff3b99dbdfb85848bb2ca6d54cf8bf67364b4c3bf377f0c3eb149bf04b3cf68c07cce0ef1cae0fa236d8d67ec1be6f54c9c7457ef3549fb1b4d', 'student');

-- Insert Woxsen University Hostel Blocks
INSERT INTO Hostel (hostel_name, hostel_type, location, warden_name, contact_phone, total_rooms) VALUES
('Woxsen Amber Girls Hostel (Block A)', 'Girls', 'Woxsen South Campus, Hyderabad', 'Dr. Sunita Rao', '+91 9845012345', 30),
('Woxsen Coral Girls Hostel (Block B)', 'Girls', 'Woxsen South Campus, Hyderabad', 'Prof. Priya Nair', '+91 9845023456', 25),
('Woxsen Ruby Girls Hostel (Block C)', 'Girls', 'Woxsen Central Campus, Hyderabad', 'Dr. Meenakshi Sharma', '+91 9845034567', 35),
('Woxsen Emerald Girls Hostel (Block D)', 'Girls', 'Woxsen East Campus, Hyderabad', 'Mrs. Lakshmi Prasad', '+91 9845045678', 30);

-- Insert Rooms
INSERT INTO Room (hostel_id, room_number, room_type, capacity, occupied, fee_per_semester, status) VALUES
(1, 'A-101', 'Double AC', 2, 2, 45000.00, 'Full'),
(1, 'A-102', 'Double AC', 2, 2, 45000.00, 'Full'),
(1, 'A-103', 'Single AC', 1, 1, 60000.00, 'Full'),
(1, 'A-104', 'Double Non-AC', 2, 1, 35000.00, 'Available'),
(2, 'B-201', 'Double AC', 2, 1, 45000.00, 'Available'),
(2, 'B-202', 'Single AC', 1, 0, 60000.00, 'Available'),
(3, 'C-101', 'Double AC', 2, 0, 45000.00, 'Available'),
(3, 'C-102', 'Single AC', 1, 0, 60000.00, 'Available'),
(4, 'D-101', 'Double AC', 2, 0, 45000.00, 'Available');

-- Insert Female Students (Woxsen University Students)
INSERT INTO Student (user_id, roll_number, name, email, phone, course, year, gender, emergency_contact, guardian_name, address) VALUES
(3, 'WU202601', 'Sruthika Reddy', 'sruthika.reddy@woxsen.edu.in', '+91 9876543201', 'B.Tech Computer Science & AI', '3rd Year', 'Female', '+91 9811122201', 'Venkat Reddy', 'Plot 45, Jubilee Hills, Hyderabad'),
(4, 'WU202602', 'Ananya Deshmukh', 'ananya.deshmukh@woxsen.edu.in', '+91 9876543202', 'B.Tech Computer Science', '3rd Year', 'Female', '+91 9811122202', 'Mahesh Deshmukh', '78 Shivajinagar, Pune'),
(5, 'WU202603', 'Kavya Sharma', 'kavya.sharma@woxsen.edu.in', '+91 9876543203', 'B.Tech Data Science', '2nd Year', 'Female', '+91 9811122203', 'Rajeev Sharma', 'Flat 304, Palm Meadows, Bengaluru'),
(6, 'WU202604', 'Sneha Patel', 'sneha.patel@woxsen.edu.in', '+91 9876543204', 'BBA Business Analytics', '2nd Year', 'Female', '+91 9811122204', 'Kishore Patel', 'B-14 Vastrapur, Ahmedabad'),
(7, 'WU202605', 'Riya Sen', 'riya.sen@woxsen.edu.in', '+91 9876543205', 'B.Des Fashion & Product Design', '1st Year', 'Female', '+91 9811122205', 'Subhash Sen', 'Salt Lake Sector V, Kolkata'),
(8, 'WU202606', 'Pooja Verma', 'pooja.verma@woxsen.edu.in', '+91 9876543206', 'MBA General Management', '1st Year', 'Female', '+91 9811122206', 'Anil Verma', 'House 12, Civil Lines, Jaipur');

-- Insert Room Allocations
INSERT INTO Room_Allocation (student_id, room_id, allocation_date, status, remarks) VALUES
(1, 1, '2026-08-01', 'Active', 'Allocated for Academic Year 2026-27'),
(2, 1, '2026-08-01', 'Active', 'Allocated for Academic Year 2026-27'),
(3, 2, '2026-08-05', 'Active', 'Allocated for Academic Year 2026-27'),
(4, 2, '2026-08-05', 'Active', 'Allocated for Academic Year 2026-27'),
(5, 3, '2026-08-10', 'Active', 'Allocated for Academic Year 2026-27'),
(6, 5, '2026-08-12', 'Active', 'Allocated for Academic Year 2026-27');

-- Insert Fees
INSERT INTO Fee (student_id, academic_term, amount, amount_paid, payment_date, status, transaction_ref, remarks) VALUES
(1, 'Fall Semester 2026', 45000.00, 45000.00, '2026-08-02', 'Paid', 'TXN-WOXSEN-90812', 'Full semester fee paid via Woxsen Portal NetBanking'),
(2, 'Fall Semester 2026', 45000.00, 25000.00, '2026-08-15', 'Partial', 'TXN-WOXSEN-90845', 'First installment received'),
(3, 'Fall Semester 2026', 45000.00, 45000.00, '2026-08-06', 'Paid', 'TXN-WOXSEN-90901', 'Paid via UPI Transfer'),
(4, 'Fall Semester 2026', 45000.00, 45000.00, '2026-08-08', 'Paid', 'TXN-WOXSEN-90915', 'Full payment verified'),
(5, 'Fall Semester 2026', 60000.00, 30000.00, '2026-08-11', 'Partial', 'TXN-WOXSEN-90940', 'Single Room first installment'),
(6, 'Fall Semester 2026', 45000.00, 0.00, NULL, 'Pending', NULL, 'Pending payment reminder sent');

-- Insert Complaints
INSERT INTO Complaint (student_id, complaint_type, title, description, priority, complaint_date, status, resolution_notes, resolved_at) VALUES
(1, 'Wi-Fi', 'High-Speed Wi-Fi connectivity in Amber Block A', 'Signal fluctuates during evening online coding and study sessions on 1st floor corridor.', 'Medium', '2026-10-01 14:30:00', 'In Progress', 'Woxsen IT Infrastructure team assigned to calibrate access point.', NULL),
(2, 'Water', 'Solar hot water temperature adjustment', 'Morning water supply in bathroom A-101 is slightly lukewarm.', 'Low', '2026-09-28 09:15:00', 'Resolved', 'Facility plumbing team calibrated the thermostat solar valve.', '2026-09-30 16:00:00'),
(3, 'Cleanliness', 'Common study lounge sanitization', 'Block A ground floor study area deep cleaning requested.', 'High', '2026-10-03 10:00:00', 'Pending', NULL, NULL),
(4, 'Electricity', 'Ceiling fan regulator replacement', 'Fan regulator knob is loose in Room A-102.', 'Medium', '2026-10-04 18:20:00', 'In Progress', 'Campus electrician scheduled for maintenance.', NULL),
(5, 'Fan/AC', 'Air Conditioner filter cleaning in Single Room A-103', 'AC cooling air flow is gentle and needs regular mesh cleaning.', 'Low', '2026-10-05 11:00:00', 'Pending', NULL, NULL);

-- Insert Leave Requests
INSERT INTO Leave_Request (student_id, leave_type, start_date, end_date, reason, emergency_contact, status, admin_remarks) VALUES
(1, 'Weekend Home', '2026-10-10', '2026-10-13', 'Visiting family in Jubilee Hills for weekend.', '+91 9811122201', 'Approved', 'Approved by Warden. Return to campus by 8:30 PM Sunday.'),
(2, 'Medical', '2026-10-06', '2026-10-08', 'Health checkup and medical consultation.', '+91 9811122202', 'Approved', 'Medical prescription verified by campus clinic.'),
(3, 'Academic/Event', '2026-10-15', '2026-10-18', 'Representing Woxsen University in National Hackathon.', '+91 9811122203', 'Pending', NULL),
(4, 'Weekend Home', '2026-10-20', '2026-10-23', 'Attending family function in hometown.', '+91 9811122204', 'Pending', NULL);

-- Insert Notices
INSERT INTO Notice (title, category, description, date_posted, posted_by, is_pinned) VALUES
('Woxsen University Hostel Curfew & Campus Shuttle Timings', 'General', 'Reminder: Woxsen South Campus hostel entry gates close strictly at 9:30 PM. The internal electric campus shuttles operate until 10:00 PM for library users.', '2026-10-02 09:00:00', 'Office of the Chief Warden', TRUE),
('Fall Semester Hostel & Mess Fee Settlement Deadline', 'Fee Deadline', 'All students with pending hostel fee dues for Fall Semester 2026 are requested to complete settlement on the Woxsen Portal before October 15.', '2026-10-03 11:30:00', 'Woxsen Accounts & Hostel Admin', TRUE),
('Annual Woxsen Sports & Cultural Fest Accommodation Guidelines', 'Events', 'Guest accommodation and inter-university tournament schedules for badminton, basketball, and indoor games are available at the student sports desk.', '2026-10-04 15:00:00', 'Woxsen Student Council', FALSE),
('Solar Water Tank Sanitization Notice', 'Maintenance', 'Scheduled maintenance and sanitization for Amber and Coral blocks overhead solar tanks this Saturday between 10 AM to 1 PM.', '2026-09-25 08:30:00', 'Campus Facilities Team', FALSE);

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

