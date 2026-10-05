# Hostel Accommodation and Student Services Management System (DBMS)

A complete, production-ready, database-driven **Hostel Accommodation and Student Services Management System** built with **Python Flask**, **MySQL**, and modern **HTML/CSS/JavaScript**.

---

## 📌 Project Overview

The **Hostel Accommodation and Student Services Management System** is a centralized DBMS platform designed to automate and streamline hostel administrative operations, student accommodation records, fee tracking, maintenance ticket resolutions, outpass leaves, and official announcements.

### Key Objectives
* Eliminate error-prone manual hostel registers and spreadsheet files.
* Provide real-time visibility into vacant and occupied beds across hostel blocks.
* Automate room allocation with relational integrity and capacity enforcement.
* Enable students to submit grievances (Water, Electricity, Wi-Fi, etc.) and track live resolution updates.
* Streamline leave application and outpass approvals.
* Manage student semester fee billing, offline counter collections, and online student payments.

---

## 🛠️ Technology Stack

| Layer | Technology | Role / Purpose |
|---|---|---|
| **Frontend** | HTML5, Modern CSS3, JavaScript (ES6+), Google Fonts, Font Awesome | Responsive UI, Glassmorphism, Modals, Dynamic Tables & Badges |
| **Backend** | Python 3.12, Flask Framework | RESTful routing, session authentication, role-based access control |
| **Database** | MySQL 8.0+ / SQLite (Zero-Setup Fallback) | Relational DBMS, Foreign Keys, Views, Integrity Constraints |
| **Database Tool** | MySQL Workbench / CLI | SQL Schema deployment, querying, database administration |
| **Security** | Werkzeug (`scrypt`/`pbkdf2:sha256`) | Secure password hashing, Session authentication |

---

## 🏗️ Relational Database Architecture

The system implements 9 relational tables with strict Foreign Key constraints and cascading actions:

```text
               ┌───────────────┐
               │     USERS     │
               └───────┬───────┘
                       │ 1:1
                       ▼
┌──────────────┐ 1:M ┌───────────────┐ 1:M ┌─────────────────┐
│    HOSTEL    ├────►│     ROOM      ├────►│ ROOM_ALLOCATION │
└──────────────┘     └───────────────┘     └────────▲────────┘
                                                    │ M:1
                                           ┌────────┴────────┐
                                           │     STUDENT     │
                                           └──┬─────┬─────┬──┘
                                      1:M ┌───┘     │     └───┐ 1:M
                                          ▼         ▼         ▼
                                       ┌─────┐ ┌─────────┐ ┌───────────────┐
                                       │ FEE │ │COMPLAINT│ │ LEAVE_REQUEST │
                                       └─────┘ └─────────┘ └───────────────┘
                                                ┌────────┐
                                                │ NOTICE │
                                                └────────┘
```

### Table Definitions
1. **`Users`**: User credentials (`username`, `password_hash`, `role`: `admin`/`warden`/`student`).
2. **`Hostel`**: Hostel building blocks (`hostel_id`, `hostel_name`, `hostel_type`, `location`, `warden_name`, `contact_phone`).
3. **`Room`**: Room numbers, types (`Single AC`, `Double Non-AC`, etc.), capacity, current occupancy, fee per semester, status.
4. **`Student`**: Personal, academic, and emergency details (`roll_number`, `name`, `email`, `phone`, `course`, `year`, `gender`, `emergency_contact`, `guardian_name`, `address`).
5. **`Room_Allocation`**: Maps student to room with `allocation_date`, `status` (`Active`, `Vacated`, `Transferred`), and remarks.
6. **`Fee`**: Semester fee records (`academic_term`, `amount`, `amount_paid`, `due_amount`, `status`: `Paid`/`Pending`/`Partial`, `transaction_ref`).
7. **`Complaint`**: Maintenance tickets categorized by `Water`, `Electricity`, `Fan/AC`, `Wi-Fi`, `Cleanliness`, `Maintenance`, with status (`Pending` ➔ `In Progress` ➔ `Resolved`) and warden remarks.
8. **`Leave_Request`**: Student outpass leave applications with start/end dates, reason, emergency contact, status (`Pending`, `Approved`, `Rejected`), and admin remarks.
9. **`Notice`**: Circulars and announcements with category (`General`, `Maintenance`, `Fee Deadline`, `Events`, `Urgent`) and priority pin option.

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
* Python 3.10+ installed
* MySQL 8.0+ (Optional: SQLite is built-in out of the box for immediate zero-config testing)
* MySQL Workbench (For database review and execution)

### 2. Install Dependencies
In your terminal, navigate to the project directory and run:
```bash
pip install -r requirements.txt
```

### 3. (Optional) Run with MySQL
1. Open **MySQL Workbench**.
2. Open the file `database.sql` and execute the script (⚡ button) to create the `hostel_management` database and seed data.
3. Configure your MySQL credentials in `.env` or in `config.py` (or through the in-app **Database Hub** page):
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=hostel_management
```

### 4. Run the Flask Web Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Credentials

For instant evaluation, the login page provides **1-Click Quick Login** buttons or you can use:

| Role | Username / Roll No | Password | Description |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Full admin & warden privileges |
| **Hostel Warden** | `warden` | `warden123` | Operational warden privileges |
| **Student (Aarav)** | `CS202601` | `student123` | Allocated to Cauvery Block A (Room A-101) |
| **Student (Ananya)** | `EE202603` | `student123` | Allocated to Yamuna Block C (Room C-101) |

---

## ✨ Features Breakdown

### 👨‍🎓 Student Portal
* **Dashboard**: Instant view of allocated room, outstanding fee dues, active complaints count, and pinned hostel circulars.
* **Room Details**: View room type, fee, hostel block location, amenities, and contact info of all roommates.
* **Fee Payment Simulator**: View fee invoices, outstanding balance, and simulate online payments (UPI/NetBanking) with instant receipt reference generation.
* **Complaints Management**: Submit tickets with category, priority, and description; track live resolution remarks from the warden.
* **Leave Requests**: Apply for outpasses (Weekend Home, Medical, Emergency) and view warden approval status.
* **Notice Board**: Read and search circulars filtered by category (Urgent, Maintenance, Events, etc.).
* **Profile Management**: Update contact phone, emergency contacts, address, and password.

### 🛡️ Warden / Admin Portal
* **Executive Dashboard**: Live KPI tiles, bed occupancy rates by hostel block, recent maintenance tickets, and pending outpasses.
* **Student Records (CRUD)**: Search, filter by branch/gender, add new students with instant room allocation, edit profiles, or delete records.
* **Rooms & Inventory**: Visual grid showing bed slots per room (green for available, red for occupied), add rooms, edit capacities, add new hostel blocks.
* **Room Allocation Engine**: Allocate unallocated students to available rooms, transfer residents between rooms, or vacate beds with automatic capacity updates.
* **Fee Collection**: Track fee defaulters, generate semester invoices, and record offline counter cash payments.
* **Complaint Resolution**: Review complaints, update status (`Pending` ➔ `In Progress` ➔ `Resolved`), and log technician resolution notes.
* **Leave Approvals**: 1-Click Approve / Reject student leave applications with custom warden remarks.
* **Notice Publishing**: Post announcements with rich categories and pin important alerts to student dashboards.
* **DBMS Reports & Analytics**: View occupancy metrics, fee collection summaries, complaint category breakdowns, and export/print reports to PDF.
* **Database Hub**: Live status of active DBMS engine, MySQL connection tester, and database table inspector.

---

## 📂 Project Structure

```text
Hostel_Management_System/
│
├── app.py                     # Main Flask Application & Routing Engine
├── config.py                  # Configuration & Environment Variables
├── db.py                      # Universal DB Manager (MySQL + SQLite Fallback)
├── database.sql               # Complete MySQL Schema & Seed Script (MySQL Workbench)
├── requirements.txt           # Python Package Dependencies
├── .env.example               # Environment Configuration Sample
├── README.md                  # Comprehensive Documentation
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── base.html              # Responsive Layout Shell with Navigation
│   ├── login.html             # Login Portal with 1-Click Demo Logins
│   ├── register.html          # Student Registration Form
│   ├── student_dashboard.html # Student Home Dashboard
│   ├── profile.html           # Student Profile Management
│   ├── room.html              # Student Room & Roommates Information
│   ├── fees.html              # Student Fee Invoices & Payment Gateway
│   ├── complaints.html        # Student Complaint Submission & Tracker
│   ├── leave.html             # Student Leave Application & History
│   ├── notices.html           # Student Notice Board with Filters
│   ├── admin_dashboard.html   # Executive Warden Dashboard & Analytics
│   ├── students.html          # Student Management & CRUD Operations
│   ├── rooms.html             # Room Inventory & Visual Bed Grid
│   ├── admin_allocations.html # Room Allocation & Transfer Engine
│   ├── admin_fees.html        # Fee Management & Payment Collection
│   ├── admin_complaints.html  # Complaint Resolution & Workflow
│   ├── admin_leave.html       # Leave Request Approvals Hub
│   ├── admin_notices.html     # Notice Board Management & Publishing
│   ├── reports.html           # Analytical DBMS Reports & Printable PDF
│   └── db_settings.html       # Database Hub & MySQL Live Connector
│
└── static/
    ├── css/
    │   └── style.css          # Modern CSS Design System (Glassmorphism, Tokens)
    └── js/
        └── main.js            # Client-Side Modals, Search Filters & Helpers
```
