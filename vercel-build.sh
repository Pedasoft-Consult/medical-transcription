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
  
  # Install packages in groups to identify problematic ones
  echo "Installing Flask and basic dependencies..."
  pip install Flask==2.2.3 Werkzeug==2.2.3 python-dotenv==1.0.0 requests==2.31.0
  
  echo "Installing Flask extensions..."
  pip install Flask-SQLAlchemy==3.0.3 Flask-JWT-Extended==4.5.2 Flask-CORS==4.0.0 Flask-Swagger-UI==4.11.1
  
  echo "Installing database packages..."
  pip install SQLAlchemy==2.0.21 alembic==1.12.0
  
  # Install psycopg2 separately as it's often problematic
  echo "Installing psycopg2-binary..."
  pip install psycopg2-binary==2.9.7
  
  echo "Installing API and utility packages..."
  pip install apispec==6.3.0 marshmallow==3.20.1 PyYAML==6.0.1 python-dateutil==2.8.2 email_validator==2.0.0 bcrypt==4.0.1 PyJWT==2.8.0
  
  echo "Installing rate limiting packages..."
  pip install Flask-Limiter==3.3.1 redis==4.6.0 limits==3.6.0
  
  echo "Installing server packages..."
  pip install gunicorn==21.2.0 uvicorn==0.23.2 httpcore==0.17.3 httpx==0.24.1
  
  echo "Installing speech and translation packages..."
  pip install SpeechRecognition==3.10.0 deep-translator==1.11.4 gTTS==2.4.0 pydub==0.25.1
  
  echo "Installing AI service packages..."
  pip install openai==0.28.1 google-cloud-speech==2.21.0 google-cloud-translate==3.11.1
  
  echo "Installing cryptography..."
  pip install cryptography==41.0.4
  
  echo "✅ Dependencies installed successfully"
fi

# Exit with success
exit 0