# Jurni Backend

A backend service for the Jurni application built with Python 3.11 and FastAPI.

## Features

- **FastAPI Framework**: High-performance async web framework
- **Firebase Authentication**: Secure user authentication and authorization
- **Firestore Database**: NoSQL document database for user profiles
- **Poetry Package Management**: Modern dependency management and packaging

## Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)
- Firebase project with Authentication and Firestore enabled

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd jurni_backend
```

### 2. Install Poetry

If you don't have Poetry installed:

```bash
# On macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or using pip
pip install poetry
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Set Up Firebase

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Authentication and Firestore Database
3. Create a service account:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Download the JSON file and place it in your project directory
4. Configure Authentication methods (Email/Password, Google, etc.)

### 5. Environment Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:
```bash
# Application Settings
PORT=8000
HOST=0.0.0.0
ENV=development

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/your/firebase-service-account-key.json
```

## Running the Application

### Development Mode

```bash
# Using Poetry
poetry run python -m app.main

# Or activate the virtual environment first
poetry shell
python -m app.main
```

### Production Mode

```bash
# Using uvicorn directly
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Project Commands

```bash
# Install new dependency
poetry add <package-name>

# Install development dependency
poetry add --group dev <package-name>

# Show dependencies
poetry show

# Update dependencies
poetry update
```

## License

This project is licensed under the MIT License.

## Support

For support and questions, please create an issue in the repository.
