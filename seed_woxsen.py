"""
Woxsen University - Hostel Accommodation and Student Services Management System
Python Database Initializer and Seeder Script
"""
from db import db

def main():
    print("=" * 70)
    print("  WOXSEN UNIVERSITY - HOSTEL DBMS DATABASE SEEDER (PYTHON)")
    print("=" * 70)
    print(f"[*] Target Database Engine: {db.engine.upper()}")
    
    # Reseed Woxsen University Data
    db.reseed_woxsen_data()
    
    print("\n[+] Verification of Seeded Data:")
    print("----------------------------------------------------------------------")
    hostels = db.fetch_all("SELECT hostel_id, hostel_name, hostel_type, total_rooms FROM Hostel")
    print(f"Hostel Blocks ({len(hostels)}):")
    for h in hostels:
        print(f"  • #{h['hostel_id']}: {h['hostel_name']} [{h['hostel_type']}]")
        
    students = db.fetch_all("SELECT student_id, roll_number, name, gender, course FROM Student")
    print(f"\nFemale Residents ({len(students)}):")
    for s in students:
        print(f"  • {s['roll_number']} - {s['name']} ({s['gender']}) | {s['course']}")

    print("----------------------------------------------------------------------")
    print("[SUCCESS] Woxsen University database is ready and active!\n")

if __name__ == '__main__':
    main()
