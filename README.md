# Jurni Backend

A backend service for the Jurni application built with Python 3.11 and FastAPI, featuring an integrated AI-powered travel planning agent using Google's Agent Development Kit (ADK).

## Features

- **FastAPI Framework**: High-performance async web framework
- **Firebase Authentication**: Secure user authentication and authorization
- **Firestore Database**: NoSQL document database for user profiles and trip data
- **AI Travel Planner Agent**: Intelligent travel planning powered by Google ADK and Gemini
- **Multi-Agent Architecture**: Specialized sub-agents for different travel phases
- **Real-time Streaming**: Server-Sent Events for real-time AI responses
- **Poetry Package Management**: Modern dependency management and packaging

## Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)
- Firebase project with Authentication and Firestore enabled
- Google Cloud Project with Vertex AI enabled (for AI travel planner)
- Google Places API key (for location services)

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
PORT=8001
HOST=0.0.0.0
ENV=development

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/your/firebase-service-account-key.json
FIREBASE_WEB_API_KEY=your-firebase-web-api-key

# Google Cloud / ADK Configuration
GOOGLE_GENAI_USE_VERTEXAI=1  # Use Vertex AI (recommended)
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Google Places API
GOOGLE_PLACES_API_KEY=your-places-api-key

# Travel Planner Agent
TRAVEL_PLANNER_SCENARIO=app/travel_planner_agent/profiles/itinerary_empty_default.json
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
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The application will be available at:
- API: http://localhost:8001
- Documentation: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## AI Travel Planner Agent

The Jurni Backend integrates an advanced AI travel planner powered by Google's Agent Development Kit (ADK) and Gemini models. The system uses a multi-agent architecture to provide comprehensive travel planning assistance.

### Agent Architecture

The travel planner consists of several specialized sub-agents:

- **Root Agent**: Orchestrates the overall travel planning process
- **Inspiration Agent**: Helps users discover destinations and activities
- **Planning Agent**: Creates detailed itineraries with flights, hotels, and activities
- **Booking Agent**: Handles reservation confirmations and payments
- **Pre-trip Agent**: Provides pre-travel information and packing lists
- **In-trip Agent**: Offers real-time assistance during the trip
- **Post-trip Agent**: Collects feedback and improves future recommendations

### Key Features

- **Personalized Recommendations**: Uses user profiles and trip history
- **Real-time Streaming**: Server-Sent Events for live AI responses
- **Session Management**: Maintains conversation context across interactions
- **Itinerary Generation**: Creates structured, bookable travel plans
- **Multi-modal Support**: Handles text, images, and structured data
- **Error Handling**: Robust error handling with graceful fallbacks

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

# Run with specific environment
GOOGLE_GENAI_USE_VERTEXAI=0 poetry run python -m app.main  # Use ML Dev
GOOGLE_GENAI_USE_VERTEXAI=1 poetry run python -m app.main  # Use Vertex AI
```

## Project Structure

```
jurni_backend/
├── app/
│   ├── auth/                    # Authentication middleware
│   ├── models/                  # Data models
│   ├── routes/                  # API endpoints
│   │   ├── auth.py             # Authentication routes
│   │   ├── trips.py            # Trip management routes
│   │   └── travel_planner.py   # AI travel planner routes
│   ├── services/                # Business logic services
│   │   ├── firebase_service.py         # Firebase integration
│   │   └── adk_travel_planner_service.py # ADK integration
│   ├── travel_planner_agent/    # AI travel planner agent
│   │   ├── agent.py            # Root agent configuration
│   │   ├── prompt.py           # Agent prompts
│   │   ├── profiles/           # Default itinerary templates
│   │   ├── sub_agents/         # Specialized sub-agents
│   │   │   ├── inspiration/    # Destination discovery
│   │   │   ├── planning/       # Itinerary creation
│   │   │   ├── booking/        # Reservation handling
│   │   │   ├── pre_trip/       # Pre-travel assistance
│   │   │   ├── in_trip/        # Real-time trip support
│   │   │   └── post_trip/      # Post-travel feedback
│   │   ├── shared_libraries/   # Common types and utilities
│   │   └── tools/              # Agent tools and utilities
│   └── main.py                 # Application entry point
├── test_adk_integration.py     # ADK integration tests
├── pyproject.toml              # Poetry configuration
├── .env.example                # Environment template
└── README.md                   # This file
```

## Configuration

### Google Cloud Setup

1. Create a Google Cloud Project
2. Enable Vertex AI API
3. Set up Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```
4. Or use a service account key file

### Google Places API

1. Enable Places API in Google Cloud Console
2. Create an API key with Places API access
3. Add the key to your `.env` file

### Environment Variables

See `.env.example` for all available configuration options.

## License

This project is licensed under the MIT License.
