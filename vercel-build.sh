#!/bin/bash

if [ -z "$VERCEL" ]; then
  echo "Running in local mode - using virtual environment"
  if [ ! -d "venv" ]; then
    python3.9 -m venv venv_py39
  fi
  source venv_py39/bin/activate
  pip install -r requirements.txt
  echo "🛠 Running database initialization script..."
  python3 api/create_postgres_tables.py
else
  echo "Running in Vercel deployment mode"
  
  # Update pip first
  pip install --upgrade pip setuptools wheel
  
  # Install all dependencies at once - more reliable for Vercel
  pip install -r requirements.txt
  
  echo "✅ Dependencies installed successfully"
  
  # Debug information
  echo "Python version: $(python --version)"
  echo "SQLAlchemy version: $(pip show sqlalchemy | grep Version)"
  echo "Flask-SQLAlchemy version: $(pip show flask-sqlalchemy | grep Version)"

  # Create necessary directories
  mkdir -p uploads
  mkdir -p tts_output
  mkdir -p tmp
fi

# Exit with success
exit 0