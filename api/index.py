"""
Vercel-compatible Student Lab Attendance System
A minimal Flask application for tracking student clock in/out times
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import urllib.parse

app = Flask(__name__)

# Get secret key from environment variable
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-in-production')

# Database connection using environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Create a database connection using PostgreSQL"""
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable not set")
    
    # Parse the database URL
    url = urllib.parse.urlparse(DATABASE_URL)
    
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],  # Remove leading slash
        user=url.username,
        password=url.password,
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    """Initialize the database with the attendance table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                matric_no TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                clock_in TEXT NOT NULL,
                clock_out TEXT
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")

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
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if action == 'clock_in':
                # Check if student already has an active session (clocked in but not out)
                cursor.execute(
                    'SELECT * FROM attendance WHERE matric_no = %s AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                    (matric_no,)
                )
                active_session = cursor.fetchone()
                
                if active_session:
                    flash(f'Error: {matric_no} is already clocked in. Please clock out first.')
                else:
                    # Create new attendance record
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    current_time = datetime.now().strftime('%H:%M:%S')
                    
                    cursor.execute(
                        'INSERT INTO attendance (matric_no, name, date, clock_in) VALUES (%s, %s, %s, %s)',
                        (matric_no, name, current_date, current_time)
                    )
                    conn.commit()
                    formatted_time = format_time_12hr(current_time)
                    flash(f'Success: {name} clocked in at {formatted_time}')
            
            elif action == 'clock_out':
                # Find the active session for this student
                cursor.execute(
                    'SELECT * FROM attendance WHERE matric_no = %s AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                    (matric_no,)
                )
                active_session = cursor.fetchone()
                
                if not active_session:
                    flash(f'Error: {matric_no} has not clocked in yet.')
                else:
                    # Update the record with clock out time
                    current_time = datetime.now().strftime('%H:%M:%S')
                    
                    cursor.execute(
                        'UPDATE attendance SET clock_out = %s WHERE id = %s',
                        (current_time, active_session['id'])
                    )
                    conn.commit()
                    formatted_time = format_time_12hr(current_time)
                    flash(f'Success: {active_session["name"]} clocked out at {formatted_time}')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            flash(f'Database error: {str(e)}')
        
        return redirect(url_for('index'))
    
    # GET request - display the page with all records
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM attendance ORDER BY date DESC, clock_in DESC')
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        records = []
        flash(f'Error loading records: {str(e)}')
    
    return render_template('index.html', records=records)

# Initialize database on first import
try:
    init_db()
except:
    # Ignore initialization errors in serverless environment
    pass

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: None)