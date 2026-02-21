# Complete Implementation Guide - Step by Step

This guide walks you through implementing and testing all features of the Zania QA Bot API.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Running the Application](#running-the-application)
4. [Testing the API](#testing-the-api)
5. [Using Docker](#using-docker)
6. [Using the Frontend](#using-the-frontend)
7. [Viewing Metrics](#viewing-metrics)
8. [Running Tests](#running-tests)

---

## Prerequisites

### Step 1: Check Python Version
```bash
python3 --version
```
**Expected**: Python 3.8 or higher

### Step 2: Verify You Have Required Tools
- Python 3.8+
- pip (Python package manager)
- Git (optional, for version control)
- Docker (optional, for containerization)

---

## Initial Setup

### Step 1: Navigate to Project Directory
```bash
cd /Users/surbhiagrawal/Desktop/Zania
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
```

**What this does**: Creates an isolated Python environment

### Step 3: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

**Verify**: Your terminal prompt should show `(venv)`

### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected output**: All packages install successfully

**Troubleshooting**: If some packages fail, try:
```bash
./install_fixed.sh
```

### Step 5: Set Up Environment Variables
```bash
./setup_env.sh
```

**Or manually:**
```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

**Verify**: Check that `.env` file exists:
```bash
cat .env
```

---

## Running the Application

### Step 1: Start the Server

**Option A: Using the run script (Recommended)**
```bash
./run.sh
```

**Option B: Manual start**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Verify Server is Running

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 3: Test Health Endpoint

**In a new terminal:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"healthy"}
```

### Step 4: Access API Documentation

Open in browser: **http://localhost:8000/docs**

You should see the Swagger UI with all available endpoints.

---

## Testing the API

### Test 1: Basic QA Request

**Prepare files:**
- `sample_questions.json` (already exists)
- `soc2-type2.pdf` (or any PDF document)

**Run the request:**
```bash
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@sample_questions.json" \
  -F "document_file=@soc2-type2.pdf" \
  -o results.json
```

**Verify:**
```bash
cat results.json
```

**Expected**: JSON with question-answer pairs

### Test 2: Test with JSON Document

**Create a JSON document:**
```bash
echo '{"content": "This is a test document about artificial intelligence and machine learning."}' > test_doc.json
```

**Create questions:**
```bash
echo '["What is this document about?"]' > test_questions.json
```

**Run request:**
```bash
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@test_questions.json" \
  -F "document_file=@test_doc.json" \
  -o results.json
```

### Test 3: Test Error Handling

**Test invalid file type:**
```bash
echo "not json" > invalid.txt
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@invalid.txt" \
  -F "document_file=@soc2-type2.pdf"
```

**Expected**: Error message about file type

**Test file size limit:**
```bash
# Create a large file (51MB)
dd if=/dev/zero of=large.txt bs=1M count=51
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@large.txt" \
  -F "document_file=@soc2-type2.pdf"
```

**Expected**: 413 error (Payload Too Large)

### Test 4: Test Multiple Questions

**Verify**: `sample_questions.json` has 5 questions

**Run:**
```bash
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@sample_questions.json" \
  -F "document_file=@soc2-type2.pdf" \
  -o results.json
```

**Check results:**
```bash
cat results.json | python3 -m json.tool
```

**Expected**: 5 question-answer pairs

---

## Using Docker

> **Note**: Docker is **optional**. You can run the application directly without Docker (see "Running the Application" section above). Docker is only needed if you want containerized deployment.

### Step 1: Install Docker (If Not Installed)

**Check if Docker is installed:**
```bash
docker --version
```

**If you get "command not found", install Docker:**

**On macOS:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install the `.dmg` file
3. Open Docker Desktop from Applications
4. Wait for Docker to start (whale icon in menu bar)
5. Verify: `docker --version`

**On Linux (Ubuntu/Debian):**
```bash
# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect

# Verify
docker --version
```

**On Windows:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install and restart computer
3. Open Docker Desktop
4. Verify: `docker --version`

### Step 2: Build Docker Image
```bash
docker build -t zania-qa-bot .
```

**Expected**: Image builds successfully

**If you get permission errors on Linux:**
```bash
sudo docker build -t zania-qa-bot .
```

**Verify:**
```bash
docker images | grep zania-qa-bot
```

### Step 3: Install Docker Compose (If Needed)

**Check if docker-compose is installed:**
```bash
docker-compose --version
```

**If not installed:**

**On macOS/Linux:**
```bash
# Usually comes with Docker Desktop, but if needed:
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Or use the newer `docker compose` command (no hyphen):**
```bash
docker compose --version
```

### Step 4: Run with Docker Compose

**Start services:**
```bash
# Try this first (newer syntax)
docker compose up --build

# Or if that doesn't work:
docker-compose up --build
```

**Expected**: Container starts and API is available

**If you get permission errors on Linux:**
```bash
sudo docker compose up --build
```

### Step 5: Test Docker Container

**In another terminal:**
```bash
curl http://localhost:8000/health
```

**Expected**: `{"status":"healthy"}`

### Step 6: View Container Logs
```bash
# Newer syntax
docker compose logs -f

# Or older syntax
docker-compose logs -f
```

**Expected**: See structured JSON logs

### Step 7: Stop Docker Container
```bash
# Newer syntax
docker compose down

# Or older syntax
docker-compose down
```

---

## Alternative: Running Without Docker

**If you don't want to install Docker, you can run the application directly:**

### Option 1: Using the Run Script (Recommended)
```bash
./run.sh
```

### Option 2: Manual Start
```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**All features work the same way - Docker is just for containerization!**

---

## Using the Frontend

### Step 1: Start the API Server
```bash
./run.sh
```

**Keep this terminal running!**

### Step 2: Open Frontend

**Option A: Direct file open**
- Navigate to `frontend/` directory
- Open `index.html` in your web browser

**Option B: Serve with Python (Better for CORS)**
```bash
cd frontend
python3 -m http.server 8080
```

Then open: **http://localhost:8080**

### Step 3: Use the Frontend

1. **Verify API URL**: Should be `http://localhost:8000`
2. **Upload Questions File**: Click "Choose File" → Select `sample_questions.json`
3. **Upload Document File**: Click "Choose File" → Select `soc2-type2.pdf`
4. **Click "Get Answers"**
5. **View Results**: Question-answer pairs displayed

### Step 4: Test Error Handling

**Test with invalid file:**
- Upload a `.txt` file as questions
- Click "Get Answers"
- **Expected**: Error message displayed

---

## Viewing Metrics

### Step 1: Make Some Requests

Run a few API requests first:
```bash
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@sample_questions.json" \
  -F "document_file=@soc2-type2.pdf"
```

### Step 2: View Metrics
```bash
curl http://localhost:8000/metrics
```

**Expected response:**
```json
{
  "metrics": {
    "total_requests": 1,
    "successful_requests": 1,
    "failed_requests": 0,
    "total_questions_processed": 5,
    "average_response_time": 2.5,
    "total_tokens_used": 0
  },
  "uptime_seconds": 120.5
}
```

### Step 3: View Structured Logs

**Check server terminal** for JSON-formatted logs:
```json
{"timestamp": "2024-01-01 12:00:00", "level": "INFO", "message": "QA processing completed", "extra_data": {...}}
```

---

## Running Tests

### Step 1: Run All Tests
```bash
source venv/bin/activate
pytest tests/ -v
```

**Expected**: All tests pass

### Step 2: Run Specific Test Suites

**Unit tests:**
```bash
pytest tests/test_document_loader.py -v
pytest tests/test_api.py -v
```

**Integration tests:**
```bash
pytest tests/test_integration.py -v
```

### Step 3: Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

**View coverage report:**
```bash
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

---

## Verifying All Features

### Feature Checklist

#### ✅ 1. Backend Correctness
- [ ] API returns valid JSON
- [ ] Supports PDF documents
- [ ] Supports JSON documents
- [ ] Handles multiple questions
- [ ] Endpoints match spec

**Test:**
```bash
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@sample_questions.json" \
  -F "document_file=@soc2-type2.pdf" | python3 -m json.tool
```

#### ✅ 2. Error Handling
- [ ] File size limits enforced (50MB)
- [ ] Question count limits (100 max)
- [ ] Clear error messages
- [ ] Graceful failure handling

**Test:**
```bash
# Test file size limit
dd if=/dev/zero of=large.pdf bs=1M count=51
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@sample_questions.json" \
  -F "document_file=@large.pdf"
# Expected: 413 error
```

#### ✅ 3. Code Quality
- [ ] Clean architecture
- [ ] Separation of concerns
- [ ] Well-documented code

**Verify:**
```bash
# Check code structure
ls -la app/
# Should see: main.py, qa_service.py, document_loader.py, config.py
```

#### ✅ 4. Tests
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Tests use mocked LLM

**Test:**
```bash
pytest tests/ -v
```

#### ✅ 5. Performance & Concurrency
- [ ] Async processing works
- [ ] Multiple questions processed concurrently
- [ ] Efficient chunking

**Test:**
```bash
# Create file with many questions
python3 -c "import json; json.dump([f'Question {i}?' for i in range(10)], open('many_questions.json', 'w'))"
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@many_questions.json" \
  -F "document_file=@soc2-type2.pdf" \
  -o results.json
# Check logs for concurrent processing
```

#### ✅ 6. Containerization & Observability
- [ ] Structured logging works
- [ ] Metrics endpoint works
- [ ] Docker builds successfully (optional - only if Docker is installed)

**Test (Without Docker):**
```bash
# Start server normally
./run.sh

# In another terminal, test metrics
curl http://localhost:8000/metrics

# Check logs in server terminal - should see JSON formatted logs
```

**Test (With Docker - Optional):**
```bash
# Only if Docker is installed
docker build -t zania-qa-bot .
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY zania-qa-bot
curl http://localhost:8000/metrics
```

#### ✅ 7. Grounding & Answer Quality
- [ ] Answers reference document content
- [ ] "Not found" when answer not in document
- [ ] Citations available

**Test:**
```bash
# Ask question not in document
echo '["What is the weather today?"]' > test_q.json
echo '{"topic": "Python programming"}' > test_doc.json
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@test_q.json" \
  -F "document_file=@test_doc.json"
# Expected: "Information not found in the provided documents"
```

#### ✅ 8. Frontend
- [ ] UI loads correctly
- [ ] File upload works
- [ ] Results display correctly

**Test:**
1. Open `frontend/index.html`
2. Upload files
3. Verify results appear

---

## Troubleshooting

### Issue: Server won't start

**Symptoms**: `ModuleNotFoundError` or import errors

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: API key error

**Symptoms**: `OPENAI_API_KEY environment variable is not set`

**Solution:**
```bash
./setup_env.sh
# Or check .env file exists
cat .env
```

### Issue: Port already in use

**Symptoms**: `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
# Or use different port
uvicorn app.main:app --port 8001
```

### Issue: Docker command not found

**Symptoms**: `docker: command not found`

**Solution:**
1. Install Docker (see "Using Docker" section above)
2. Or skip Docker entirely - all features work without it!
3. Use: `./run.sh` instead

### Issue: Docker build fails

**Symptoms**: Build errors

**Solution:**
```bash
# Check Docker is running
docker ps
# If error, start Docker Desktop (macOS/Windows) or Docker service (Linux)
# Rebuild without cache
docker build --no-cache -t zania-qa-bot .
```

### Issue: Docker permission denied (Linux)

**Symptoms**: `permission denied while trying to connect to the Docker daemon socket`

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in, or:
newgrp docker
# Or use sudo (not recommended for production)
sudo docker build -t zania-qa-bot .
```

### Issue: Tests fail

**Symptoms**: Test failures

**Solution:**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx
# Run with verbose output
pytest tests/ -v -s
```

### Issue: Frontend can't connect

**Symptoms**: CORS errors or connection refused

**Solution:**
1. Verify API is running: `curl http://localhost:8000/health`
2. Check API URL in frontend matches server URL
3. Serve frontend with Python: `python3 -m http.server 8080`

---

## Quick Reference Commands

### Start Server
```bash
./run.sh
```

### Test API
```bash
curl -X POST "http://localhost:8000/qa" \
  -F "questions_file=@sample_questions.json" \
  -F "document_file=@soc2-type2.pdf"
```

### View Metrics
```bash
curl http://localhost:8000/metrics
```

### Run Tests
```bash
pytest tests/ -v
```

### Docker (Optional)
```bash
# If Docker is installed
docker compose up --build
# Or
docker-compose up --build

# If Docker is NOT installed, just use:
./run.sh
```

### View Logs
```bash
# Server logs (in terminal running server)
# Or Docker logs
docker-compose logs -f
```

---


---

## Getting Help

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review server logs for error messages
3. Verify all prerequisites are met
4. Check that `.env` file exists with API key
5. Ensure virtual environment is activated

---

