# Gemini Report Generator - Frontend & Backend

A complete system for generating reports using Google Gemini API with a web interface.

## 📋 Project Structure

```
Gemini/
├── app.py                 # Backend Flask API server
├── index.html             # Frontend web interface
├── test.py               # Original Gemini API test
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Features

- **Web-based Interface**: Beautiful, responsive frontend for easy interaction
- **REST API Backend**: Flask-based API server with `/api/ask` endpoint
- **Gemini Integration**: Uses Google Gemini 3-Flash model for responses
- **Real-time Processing**: Send questions and get instant responses
- **Error Handling**: Comprehensive error handling and user feedback

## 📦 Installation

All required packages are already installed. If you need to reinstall:

```bash
pip install -r requirements.txt
```

### Required Packages
- `google-genai` - Google Gemini API client
- `flask` - Web framework
- `flask-cors` - Cross-Origin Resource Sharing support

## 🏃 Running the Application

### Start the Backend Server

```bash
python app.py
```

The server will start on `http://127.0.0.1:5000`

You'll see output like:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Access the Frontend

Once the backend is running, open your browser and visit:

```
http://127.0.0.1:5000
```

## 🔌 API Endpoints

### `POST /api/ask`
Send a question to Gemini and get a response.

**Request:**
```json
{
    "question": "Explain how AI works in a few words"
}
```

**Response (Success):**
```json
{
    "success": true,
    "question": "Explain how AI works in a few words",
    "response": "AI works by processing data through neural networks that learn patterns..."
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Error message describing what went wrong"
}
```

### `GET /api/health`
Health check endpoint to verify the server is running.

**Response:**
```json
{
    "status": "ok"
}
```

### `GET /`
Serves the main frontend HTML interface.

## 🎨 Frontend Features

- Clean, modern UI with gradient background
- Real-time loading indicator while processing
- Success and error messages
- Displays both the question and formatted response
- Responsive design for mobile and desktop
- Clear button to reset the form

## 🔑 API Key

The Gemini API key is embedded in `app.py`. For production use, consider:
1. Moving the API key to environment variables
2. Using a `.env` file
3. Implementing proper authentication

Update this line in `app.py`:
```python
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
```

## 📝 Usage Examples

### From Frontend
1. Open http://127.0.0.1:5000 in your browser
2. Enter your question in the textarea
3. Click "Send Request"
4. Wait for the response to appear

### From Command Line
```bash
curl -X POST http://127.0.0.1:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'
```

## 🛠️ Development

To modify the system:
- Edit `app.py` to change backend logic
- Edit `index.html` to change the frontend UI
- The `test.py` file can be used for testing Gemini API independently

## ⚠️ Troubleshooting

**Port 5000 already in use:**
```bash
python app.py  # Will automatically find another port
```

**CORS errors:**
- The app uses `flask-cors` to handle cross-origin requests
- Ensure the frontend is accessing `http://127.0.0.1:5000/api/ask`

**Gemini API errors:**
- Check that your API key is valid
- Ensure you have access to the `gemini-3-flash-preview` model

## 📚 Model Information

The application uses:
- **Model**: `gemini-3-flash-preview`
- **API**: Google GenAI Python client

## 🎯 Future Enhancements

- Add report formatting options
- Implement caching for repeated questions
- Add conversation history
- Support for multiple Gemini models
- Database integration for saving reports
- User authentication

## 📄 License

This project uses the Google Gemini API. Ensure you comply with their terms of service.
