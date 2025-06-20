# Regex Pattern Matcher

AI-powered text pattern replacement for CSV and Excel files using natural language input.

## Demo
[![Demo Video](https://img.youtube.com/vi/SMoFBOFIw0A/maxresdefault.jpg)](https://youtu.be/SMoFBOFIw0A)

## Tech Stack
- **Backend**: Django + Pandas + Hugging Face API
- **Frontend**: React + Tailwind CSS

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+

### Backend (Django)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend (React)
```bash
cd frontend
npm install
# Update API URLs in React code to match backend port
npm start
```

## Usage
1. Upload CSV/Excel file
2. Enter natural language command:
   - "Replace emails with REDACTED"
   - "Make Name column null"
   - "Find phone numbers and replace with [PHONE]"
3. Download processed file

## Project Structure
```
├── backend/          # Django API
├── frontend/         # React app
├── test_data.csv     # Sample data
└── README.md
```

## Configuration
- Hugging Face API token is configured in `backend/views.py`
- Update frontend API URLs to match backend port (default: http://localhost:8000)
