"""
Simple Student Lab Attendance System
A minimal Flask application for tracking student clock in/out times
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import os

# Load environment variables from .env file for local development (if available)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Use environment variable

# Database file path
DATABASE = 'attendance.db'

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with the attendance table"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matric_no TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            clock_in TEXT NOT NULL,
            clock_out TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database when app starts
init_db()

def format_time_12hr(time_str):
    """Convert 24-hour time to 12-hour format with AM/PM"""
    if not time_str:
        return None
    try:
        time_obj = datetime.strptime(time_str, '%H:%M:%S')
        return time_obj.strftime('%I:%M %p')
    except:
        return time_str

app.jinja_env.filters['format_time_12hr'] = format_time_12hr

# Clearing behavior for local dev (SQLite): use CLEAR_MODE env var ('always' or 'per_day')
CLEAR_MODE = os.environ.get('CLEAR_MODE', 'per_day').strip().lower()

def maybe_clear_records(conn):
    """Clear attendance records based on CLEAR_MODE.
    - 'always': clear all records on every new clock_in
    - 'per_day': if last record is not today, clear all before starting a new day
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        cur = conn.cursor()
        if CLEAR_MODE == 'always':
            cur.execute('DELETE FROM attendance')
            conn.commit()
            cur.close()
            return
        elif CLEAR_MODE == 'per_day':
            cur.execute('SELECT date FROM attendance ORDER BY id DESC LIMIT 1')
            row = cur.fetchone()
            if row:
                last_date = row[0]
                if last_date != today:
                    cur.execute('DELETE FROM attendance')
                    conn.commit()
            cur.close()
    except Exception as e:
        print(f"maybe_clear_records error: {e}")
@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page - handles clock in, clock out, and displays records"""
    
    if request.method == 'POST':
        action = request.form.get('action')
        matric_no = request.form.get('matric_no', '').strip()
        name = request.form.get('name', '').strip()

        if action == 'clock_in' and (not matric_no or not name):
            flash('Please enter both Matric No and Name')
            return redirect(url_for('index'))
        elif action == 'clock_out' and not matric_no:
            flash('Please enter Matric No')
            return redirect(url_for('index'))

        conn = get_db_connection()

        if action == 'clock_in':
            # Clear records if needed before starting a new session
            maybe_clear_records(conn)
            # Check if student already has an active session (clocked in but not out)
            active_session = conn.execute(
                'SELECT * FROM attendance WHERE matric_no = ? AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                (matric_no,)
            ).fetchone()

            if active_session:
                flash(f'Error: {matric_no} is already clocked in. Please clock out first.')
            else:
                # Create new attendance record
                current_date = datetime.now().strftime('%Y-%m-%d')
                current_time = datetime.now().strftime('%H:%M:%S')

                conn.execute(
                    'INSERT INTO attendance (matric_no, name, date, clock_in) VALUES (?, ?, ?, ?)',
                    (matric_no, name, current_date, current_time)
                )
                conn.commit()
                formatted_time = format_time_12hr(current_time)
                flash(f'Success: {name} clocked in at {formatted_time}')

        elif action == 'clock_out':
            # Find the active session for this student
            active_session = conn.execute(
                'SELECT * FROM attendance WHERE matric_no = ? AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                (matric_no,)
            ).fetchone()

            if not active_session:
                flash(f'Error: {matric_no} has not clocked in yet.')
            else:
                # Update the record with clock out time
                current_time = datetime.now().strftime('%H:%M:%S')

                conn.execute(
                    'UPDATE attendance SET clock_out = ? WHERE id = ?',
                    (current_time, active_session['id'])
                )
                conn.commit()
                formatted_time = format_time_12hr(current_time)
                flash(f'Success: {active_session["name"]} clocked out at {formatted_time}')

    conn.close()
    return redirect(url_for('index'))
    
    # GET request - display the page with all records
    conn = get_db_connection()
    # Fresh-per-browser: on first GET in a new browser session, clear then mark as seen
    if CLEAR_MODE == 'always' and not session.get('seen'):
        maybe_clear_records(conn)
        session['seen'] = True
    records = conn.execute(
        'SELECT * FROM attendance ORDER BY date DESC, clock_in DESC'
    ).fetchall()
    conn.close()
    
    return render_template('index.html', records=records)

if __name__ == '__main__':
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
