# Tea Reviews

A web application for reviewing and sharing experiences with different teas. Users can add reviews, upload photos, and discover new teas through a searchable database.

## Features

- User authentication (register/login)
- Add and browse tea reviews
- Upload photos of teas
- Search functionality
- Comment on reviews
- Track tea vendors and producers

## Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

4. Run the development server:
```bash
python app.py
```

## Production Deployment

The application is configured for deployment on Render.com:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

Environment variables will be automatically configured through render.yaml.
