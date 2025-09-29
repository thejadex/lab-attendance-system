# Vercel Deployment Setup Guide

This guide will help you deploy your Flask attendance app to Vercel without crashes.

## 1. Database Setup

Since Vercel is serverless, SQLite won't work. You need a cloud database. Here are some options:

### Option A: Neon (PostgreSQL) - Recommended
1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new database
3. Copy the connection string (it looks like: `postgresql://username:password@hostname/database`)

### Option B: Supabase (PostgreSQL)
1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to Settings > Database and copy the connection string

### Option C: PlanetScale (MySQL) - Alternative
If you prefer MySQL, you can use PlanetScale and modify the code accordingly.

## 2. Environment Variables Setup

In your Vercel dashboard:

1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add these variables:

```
DATABASE_URL = your_postgresql_connection_string
SECRET_KEY = a-random-secret-key-for-flask-sessions
FLASK_ENV = production
```

## 3. Project Structure

Your project should now have this structure:
```
labAttendance/
├── api/
│   └── index.py          # Main Flask app (Vercel-compatible)
├── templates/
│   └── index.html        # Your HTML template
├── app.py               # Original app (keep for local development)
├── vercel.json          # Vercel configuration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── DEPLOYMENT.md        # This file
```

## 4. Deployment Steps

1. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will auto-detect it's a Python project

2. **Set Environment Variables:**
   - In Vercel dashboard, go to Settings > Environment Variables
   - Add DATABASE_URL and SECRET_KEY

3. **Deploy:**
   - Push your code to GitHub
   - Vercel will automatically deploy

## 5. Key Changes Made

1. **Database:** Switched from SQLite to PostgreSQL
2. **File Structure:** Moved Flask app to `api/index.py` for Vercel compatibility
3. **Error Handling:** Added proper try-catch blocks for database operations
4. **Environment Variables:** Use environment variables instead of hardcoded values

## 6. Local Development

For local development, you can still use `app.py`:

1. Copy `.env.example` to `.env`
2. Fill in your database credentials
3. Run: `python app.py`

## 7. Troubleshooting

- **500 Error:** Check environment variables are set correctly
- **Database Connection Error:** Verify DATABASE_URL format
- **Module Import Error:** Ensure all dependencies are in requirements.txt

## 8. Security Notes

- Never commit your `.env` file
- Use strong, random secret keys
- Regularly rotate your database credentials