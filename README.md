# Student Lab Attendance System

A minimal Flask-based attendance tracking system for student labs. Students can clock in and out, and view all attendance records on a single page.

## Features

- **Clock In**: Students enter their Matric No and Name to clock in
- **Clock Out**: Students enter their Matric No and Name to clock out
- **Validation**: Prevents double clock-ins and ensures students clock in before clocking out
- **Records View**: View all attendance records in a simple table on the same page
- **Single Page**: Everything (clock in, clock out, records) on one page

## Tech Stack

- **Framework**: Flask (Python)
- **Database**: SQLite
- **Styling**: None (minimal HTML)

## Local Development Setup

### Prerequisites

- Python 3.8+ installed
- pip (Python package manager)

### Step 1: Download the Project

Download the project files to your local machine.

### Step 2: Install Dependencies

Open a terminal in the project directory and run:

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### Step 3: Run the Application

\`\`\`bash
python app.py
\`\`\`

The application will start on `http://localhost:5000`

Open your browser and go to `http://localhost:5000` to use the attendance system.

### Step 4: Using the System

1. **To Clock In**:
   - Enter your Matric No (e.g., "A12345")
   - Enter your Name
   - Click "Clock In"

2. **To Clock Out**:
   - Enter your Matric No (same as when you clocked in)
   - Enter your Name
   - Click "Clock Out"

3. **View Records**:
   - All attendance records are displayed in the table at the bottom of the page
   - Records show Matric No, Name, Date, Clock In time, and Clock Out time

## Database

The application uses SQLite and automatically creates an `attendance.db` file in the project directory when you first run it.

### Database Schema

The `attendance` table structure:

\`\`\`
- id: INTEGER (Primary Key, Auto-increment)
- matric_no: TEXT (Student's Matric Number)
- name: TEXT (Student's Name)
- date: TEXT (Date in YYYY-MM-DD format)
- clock_in: TEXT (Clock in time in HH:MM:SS format)
- clock_out: TEXT (Clock out time in HH:MM:SS format, NULL if not clocked out)
\`\`\`

## Deploying to Vercel

**Important Note**: SQLite databases don't persist on Vercel's serverless platform. Each deployment creates a fresh database. For production use on Vercel, you would need to switch to a cloud database like PostgreSQL (Supabase, Neon) or use Vercel's KV storage.

### If you still want to deploy for testing:

1. Make sure you have a `vercel.json` file (already included)
2. Install Vercel CLI:
   \`\`\`bash
   npm install -g vercel
   \`\`\`
3. Deploy:
   \`\`\`bash
   vercel
   \`\`\`
4. Follow the prompts to deploy

**Limitation**: The database will reset on each deployment and won't persist data between serverless function invocations.

### Recommended for Production

For a production deployment on Vercel, consider:
1. Using a cloud database (PostgreSQL via Supabase or Neon)
2. Modifying the code to use the cloud database instead of SQLite
3. Or deploy to a traditional hosting service that supports persistent file storage (like PythonAnywhere, Heroku, or a VPS)

## Troubleshooting

### "Already clocked in" error
- You need to clock out before clocking in again
- Check the records table to see if you have an active session (no clock out time)

### "Has not clocked in yet" error
- You need to clock in before you can clock out
- Make sure you're using the correct Matric No

### Database file not found
- The database is created automatically when you first run the app
- Make sure you have write permissions in the project directory

## File Structure

\`\`\`
.
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Single page HTML template
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel deployment configuration
├── .gitignore           # Git ignore file
└── README.md            # This file
\`\`\`

## License

MIT
