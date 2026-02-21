# Frontend UI

A minimal web interface for the Zania QA Bot API.

## Usage

1. Start the API server:
   ```bash
   ./run.sh
   ```

2. Open `index.html` in your web browser

3. Configure API URL (default: http://localhost:8000)

4. Upload your files:
   - Questions file (JSON)
   - Document file (PDF or JSON)

5. Click "Get Answers" and view results

## Features

- Simple, clean interface
- File upload for questions and documents
- Real-time results display
- Error handling
- Configurable API endpoint

## Serving with Python (Optional)

For better CORS handling, you can serve the frontend:

```bash
cd frontend
python3 -m http.server 8080
```

Then open: http://localhost:8080
