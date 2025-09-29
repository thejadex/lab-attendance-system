import sqlite3
import datetime
from typing import Optional

# Database file name
DB_FILE = "lab_attendance.db"

def init_database():
    """Initialize the SQLite database and create the attendance table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create attendance table with clock_in and clock_out in the same record
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            clock_in_time TEXT NOT NULL,
            clock_out_time TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_active_session(student_id: str) -> Optional[int]:
    """Check if a student has an active session (clocked in but not clocked out)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id FROM attendance 
        WHERE student_id = ? AND clock_out_time IS NULL
    ''', (student_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def clock_in():
    """Register a student's clock-in time."""
    print("\n--- Clock In ---")
    student_id = input("Enter Student ID: ").strip()
    
    if not student_id:
        print("Error: Student ID cannot be empty.")
        return
    
    # Check if student already has an active session
    if get_active_session(student_id):
        print(f"Error: Student {student_id} is already clocked in. Please clock out first.")
        return
    
    name = input("Enter Student Name: ").strip()
    
    if not name:
        print("Error: Name cannot be empty.")
        return
    
    # Get current date and time
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    clock_in_time = now.strftime("%H:%M:%S")
    
    # Insert new attendance record
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO attendance (student_id, name, date, clock_in_time, clock_out_time)
        VALUES (?, ?, ?, ?, NULL)
    ''', (student_id, name, date, clock_in_time))
    
    conn.commit()
    conn.close()
    
    print(f"Success: {name} (ID: {student_id}) clocked in at {clock_in_time} on {date}")

def clock_out():
    """Register a student's clock-out time."""
    print("\n--- Clock Out ---")
    student_id = input("Enter Student ID: ").strip()
    
    if not student_id:
        print("Error: Student ID cannot be empty.")
        return
    
    # Check if student has an active session
    session_id = get_active_session(student_id)
    
    if not session_id:
        print(f"Error: Student {student_id} is not clocked in. Please clock in first.")
        return
    
    # Update the record with clock-out time
    now = datetime.datetime.now()
    clock_out_time = now.strftime("%H:%M:%S")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE attendance 
        SET clock_out_time = ?
        WHERE id = ?
    ''', (clock_out_time, session_id))
    
    conn.commit()
    
    # Get student name for confirmation
    cursor.execute('SELECT name FROM attendance WHERE id = ?', (session_id,))
    name = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"Success: {name} (ID: {student_id}) clocked out at {clock_out_time}")

def view_records():
    """Display all attendance records in a neat table format."""
    print("\n--- Attendance Records ---")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT student_id, name, date, clock_in_time, clock_out_time
        FROM attendance
        ORDER BY date DESC, clock_in_time DESC
    ''')
    
    records = cursor.fetchall()
    conn.close()
    
    if not records:
        print("No attendance records found.")
        return
    
    # Print table header
    print(f"{'StudentID':<12} | {'Name':<20} | {'Date':<12} | {'Clock-In':<10} | {'Clock-Out':<10}")
    print("-" * 80)
    
    # Print each record
    for record in records:
        student_id, name, date, clock_in, clock_out = record
        clock_out_display = clock_out if clock_out else "---"
        print(f"{student_id:<12} | {name:<20} | {date:<12} | {clock_in:<10} | {clock_out_display:<10}")
    
    print(f"\nTotal records: {len(records)}")

def display_menu():
    """Display the main menu options."""
    print("\n" + "=" * 40)
    print("  Student Lab Attendance System")
    print("=" * 40)
    print("1. Clock In")
    print("2. Clock Out")
    print("3. View Attendance Records")
    print("4. Exit")
    print("=" * 40)

def main():
    """Main program loop."""
    # Initialize database
    init_database()
    
    print("Welcome to the Student Lab Attendance System")
    
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            clock_in()
        elif choice == "2":
            clock_out()
        elif choice == "3":
            view_records()
        elif choice == "4":
            print("\nExiting system. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()
