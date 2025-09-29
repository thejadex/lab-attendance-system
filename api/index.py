"""
Vercel-compatible Student Lab Attendance System
A minimal Flask application for tracking student clock in/out times
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
from datetime import datetime
import urllib.parse

# Prefer psycopg (v3); fallback to psycopg2 if available
USE_PG3 = False
try:
    import psycopg
    from psycopg.rows import dict_row
    USE_PG3 = True
except Exception:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except Exception:
        psycopg2 = None

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'templates'))
app = Flask(__name__, template_folder=TEMPLATES_DIR)

# Get secret key from environment variable
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-in-production')

# Database connection using environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith(('postgres://', 'postgresql://')))

def get_db_connection():
    """Create a database connection.
    - If DATABASE_URL provided, use PostgreSQL
    - Else, fallback to SQLite at /tmp/attendance.db (ephemeral on Vercel)
    """
    if USE_POSTGRES:
        if USE_PG3:
            # psycopg v3 supports direct URL
            conn = psycopg.connect(DATABASE_URL)
            return conn
        elif psycopg2 is not None:
            url = urllib.parse.urlparse(DATABASE_URL)
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port,
                database=url.path[1:],
                user=url.username,
                password=url.password,
                cursor_factory=RealDictCursor
            )
            return conn
        else:
            raise RuntimeError("PostgreSQL driver not installed. Install psycopg[binary] or psycopg2-binary.")
    else:
        db_path = '/tmp/attendance.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize the database with the attendance table"""
    try:
        conn = get_db_connection()
        if USE_POSTGRES:
            cursor = conn.cursor() if not USE_PG3 else conn.cursor()
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
        else:
            cursor = conn.cursor()
            cursor.execute('''
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

# Clearing behavior: CLEAR_MODE can be 'always' or 'per_day' (default 'per_day')
CLEAR_MODE = os.environ.get('CLEAR_MODE', 'per_day').strip().lower()

def maybe_clear_records(conn):
    """Clear attendance records based on CLEAR_MODE.
    - 'always': clear all records on every new clock_in
    - 'per_day': if any existing record is not for today, clear all before starting a new day
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        cur = conn.cursor(row_factory=dict_row) if (USE_POSTGRES and USE_PG3) else conn.cursor()
        if CLEAR_MODE == 'always':
            cur.execute('DELETE FROM attendance')
            conn.commit()
            cur.close()
            return
        elif CLEAR_MODE == 'per_day':
            # Check if there are records from a previous day
            cur.execute('SELECT date FROM attendance ORDER BY id DESC LIMIT 1')
            row = cur.fetchone()
            if row:
                last_date = row['date'] if isinstance(row, dict) else row[0]
                if last_date != today:
                    cur.execute('DELETE FROM attendance')
                    conn.commit()
            cur.close()
    except Exception as e:
        # Don't block attendance on clear errors
        print(f"maybe_clear_records error: {e}")

@app.route('/health')
def health():
    return 'ok', 200

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
            # Clear records if needed before starting a new session
            maybe_clear_records(conn)
            cursor = conn.cursor(row_factory=dict_row) if (USE_POSTGRES and USE_PG3) else conn.cursor()

            if action == 'clock_in':
                # Check if student already has an active session (clocked in but not out)
                if USE_POSTGRES and not USE_PG3:
                    cursor.execute(
                        'SELECT * FROM attendance WHERE matric_no = %s AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                        (matric_no,)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM attendance WHERE matric_no = ? AND clock_out IS NULL ORDER BY id DESC LIMIT 1' if not USE_POSTGRES else 'SELECT * FROM attendance WHERE matric_no = %s AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                        (matric_no,)
                    )
                active_session = cursor.fetchone()

                if active_session:
                    # Note: sqlite3.Row is dict-like; psycopg2 RealDictCursor returns dict
                    flash(f'Error: {matric_no} is already clocked in. Please clock out first.')
                else:
                    # Create new attendance record
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    current_time = datetime.now().strftime('%H:%M:%S')

                    if USE_POSTGRES and not USE_PG3:
                        cursor.execute(
                            'INSERT INTO attendance (matric_no, name, date, clock_in) VALUES (%s, %s, %s, %s)',
                            (matric_no, name, current_date, current_time)
                        )
                    else:
                        cursor.execute(
                            'INSERT INTO attendance (matric_no, name, date, clock_in) VALUES (?, ?, ?, ?)' if not USE_POSTGRES else 'INSERT INTO attendance (matric_no, name, date, clock_in) VALUES (%s, %s, %s, %s)',
                            (matric_no, name, current_date, current_time)
                        )
                    conn.commit()
                    formatted_time = format_time_12hr(current_time)
                    flash(f'Success: {name} clocked in at {formatted_time}')

            elif action == 'clock_out':
                # Find the active session for this student
                if USE_POSTGRES and not USE_PG3:
                    cursor.execute(
                        'SELECT * FROM attendance WHERE matric_no = %s AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                        (matric_no,)
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM attendance WHERE matric_no = ? AND clock_out IS NULL ORDER BY id DESC LIMIT 1' if not USE_POSTGRES else 'SELECT * FROM attendance WHERE matric_no = %s AND clock_out IS NULL ORDER BY id DESC LIMIT 1',
                        (matric_no,)
                    )
                active_session = cursor.fetchone()

                if not active_session:
                    flash(f'Error: {matric_no} has not clocked in yet.')
                else:
                    # Update the record with clock out time
                    current_time = datetime.now().strftime('%H:%M:%S')

                    rec_id = active_session['id'] if isinstance(active_session, dict) else active_session['id']
                    rec_name = active_session['name'] if isinstance(active_session, dict) else active_session['name']
                    if USE_POSTGRES and not USE_PG3:
                        cursor.execute('UPDATE attendance SET clock_out = %s WHERE id = %s', (current_time, rec_id))
                    else:
                        cursor.execute('UPDATE attendance SET clock_out = ? WHERE id = ?' if not USE_POSTGRES else 'UPDATE attendance SET clock_out = %s WHERE id = %s', (current_time, rec_id))
                    conn.commit()
                    formatted_time = format_time_12hr(current_time)
                    flash(f'Success: {rec_name} clocked out at {formatted_time}')

            cursor.close()
            conn.close()

        except Exception as e:
            flash(f'Database error: {str(e)}')
        
    return redirect(url_for('index'))
    
    # GET request - display the page with all records
    try:
        conn = get_db_connection()
        # Fresh-per-browser: on first GET in a new browser session, clear then mark as seen
        if CLEAR_MODE == 'always':
            if not session.get('seen'):  # first visit in this browser
                maybe_clear_records(conn)
                session['seen'] = True
        cursor = conn.cursor(row_factory=dict_row) if (USE_POSTGRES and USE_PG3) else conn.cursor()
        cursor.execute('SELECT * FROM attendance ORDER BY date DESC, clock_in DESC')
        rows = cursor.fetchall()
        # Normalize to list of dicts for template compatibility
        if USE_POSTGRES and not USE_PG3:
            records = rows  # already dict rows via RealDictCursor
        else:
            records = [dict(row) for row in rows] if rows and not isinstance(rows[0], dict) else rows
        cursor.close()
        conn.close()
    except Exception as e:
        records = []
        flash(f'Error loading records: {str(e)}')
    
    resp = app.make_response(render_template('index.html', records=records))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

# Initialize database on first import
try:
    init_db()
except:
    # Ignore initialization errors in serverless environment
    pass

# No custom handler needed; Vercel detects the Flask `app` WSGI application