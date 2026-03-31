# How to Run the Project

This project contains two main parts: a Python backend and a Next.js frontend. They have been separated into their respective directories: `backend/` and `frontend/`.

## Prerequisites
- **Python 3.9+** (for the backend)
- **Node.js 18+** (for the frontend)
- **Redis** (for Celery workers) or Docker if using `docker-compose`

---

## Running Locally (Without Docker)

To run the project locally, open **three separate terminal windows** (from the root of the project). You can copy and paste the entire block of commands below into each respective terminal to run them all at once.

### Terminal 1: Backend Setup & API Server
This will install Redis, configure your environment, install dependencies, and start the FastAPI server.

```bash
# Ensure Redis is installed and running (macOS Homebrew)
brew install redis
brew services start redis

# Setup Python environment and install dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment variables to use local Redis
cp ../.env.example .env
sed -i.bak 's/redis:\/\/redis:6379/redis:\/\/localhost:6379/g' .env

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*(The API will be available at http://localhost:8000)*

### Terminal 2: Celery Worker
This will activate the environment and start the background task worker.

```bash
cd backend
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

### Terminal 3: Frontend Setup & Server
This will install Node dependencies and start the Next.js frontend.

```bash
cd frontend
npm install
npm run dev
```
*(The frontend will be available at http://localhost:3000)*

---

## Docker Compose (Alternative)

If you prefer to run the entire backend stack via Docker instead of natively, you can do it all in a single terminal window:

```bash
cd backend
docker-compose up --build
```
