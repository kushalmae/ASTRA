# ASTRA - Automated Satellite Threshold Reporting & Alerts

Code tutorial - https://code2tutorial.com/tutorial/c96510f4-7bb6-40e6-99e2-768004663b8e/index.md

ASTRA is a web application for monitoring satellite payload metrics and alerting on threshold breaches.

## Features

- Real-time monitoring of satellite payload metrics
- Configurable thresholds for different metric types
- Dashboard with current status and breach history
- Detailed event history with filtering and sorting
- API endpoints for integration with other systems

## Project Structure

### Overview
ASTRA (Automated Satellite Threshold Reporting & Alerts) is a web application for monitoring satellite payload metrics and alerting on threshold breaches. It integrates with MATLAB for satellite metrics processing.

### Directory Structure

#### Root Directory
- `app.py`: Main entry point for the application
- `app/`: Core application code
- `config/`: Configuration files for the application
- `data/`: Storage for application data
- `logs/`: Application logs
- `matlab_scripts/`: MATLAB scripts for satellite metrics processing
- `requirements/`: Python dependencies for different environments
- `venv/`: Python virtual environment (not tracked in git)

#### App Directory (`app/`)
```
app/
├── __init__.py         # Application factory and initialization
├── config/             # Application configuration settings
├── database/           # Database connections and operations
├── models/             # SQLAlchemy ORM models
├── routes/             # URL routing definitions
├── services/           # Business logic services
├── static/             # Static assets (CSS, JS, images)
├── templates/          # HTML templates
├── utils/              # Utility functions and helpers
└── views/              # View functions
```

### Key Components

#### Models
- `Payload`: Represents satellite payloads with IDs, names, and status
- `Event`: Records monitoring events with metrics and threshold breaches
- `BreachHistory`: Tracks history of threshold breaches

#### Services
- `matlab_interface.py`: Integration with MATLAB for processing satellite metrics
- `monitor_service.py`: Service for monitoring satellite metrics
- `event_service.py`: Service for managing monitoring events

#### Database
- Uses SQLAlchemy ORM for database operations
- Models define relationships between satellites, events, and breach history

### Application Flow
1. The app starts a background monitoring thread
2. The monitoring system periodically checks satellite metrics using MATLAB
3. When thresholds are breached, events are stored in the database
4. The web interface displays current status and breach history
5. API endpoints provide programmatic access to the system

### Configuration Options
Environment variables control application behavior
Simulation mode available for testing without MATLAB
Configurable logging levels and database settings
Adjustable refresh intervals for monitoring

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/astra.git
   cd astra
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   # For development
   pip install -r requirements/dev.txt
   
   # For production
   pip install -r requirements/prod.txt
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Run the application:
   ```bash
   # Development
   flask run
   
   # Production
   gunicorn "app:create_app()"
   ```

## Configuration

The application is configured using the `config/metrics_config.json` file:

```json
{
  "metrics": {
    "thermal": {"threshold": 75.0},
    "voltage": {"threshold": 3.3},
    "latency": {"threshold": 250}
  },
  "payloads": [
    {"scid": 101, "name": "Payload 1"},
    {"scid": 102, "name": "Payload 2"}
  ],
  "environment": {
    "FLASK_ENV": "development",
    "DATABASE_PATH": "./data/astra.db",
    "LOG_LEVEL": "INFO",
    "USE_SIMULATION": "False",
    "LOGGING_ENABLED": "True",
    "MATLAB_SCRIPTS_PATH": "./matlab_scripts",
    "REFRESH_INTERVAL": "600"
  }
}
```

The configuration includes:
- `metrics`: Defines the metrics and their threshold values
- `payloads`: Lists all spacecraft payloads being monitored
- `environment`: System configuration that was previously set with environment variables:
  - `FLASK_ENV`: Environment (development/production)
  - `DATABASE_PATH`: Path to the SQLite database
  - `SECRET_KEY`: Application secret key
  - `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
  - `USE_SIMULATION`: Set to "True" to run in simulation mode without MATLAB
  - `LOGGING_ENABLED`: Set to "False" to disable all logging
  - `MATLAB_SCRIPTS_PATH`: Path to the MATLAB scripts directory
  - `REFRESH_INTERVAL`: Interval in seconds between metric checks

You can still use environment variables for backward compatibility, but the values in the config file take precedence.

## API Documentation

### Events API

- `GET /api/events`: Get paginated events with filtering
- `GET /api/breach_history`: Get breach history for a specific payload and metric

### Monitor API

- `POST /api/monitor`: Submit new metric data for monitoring

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .
isort .

# Check code quality
flake8
mypy .
```

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
