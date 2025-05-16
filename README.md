# ASTRA - Automated Satellite Threshold Reporting & Alerts

ASTRA is a web application for monitoring satellite payload metrics and alerting on threshold breaches.

## Features

- Real-time monitoring of satellite payload metrics
- Configurable thresholds for different metric types
- Dashboard with current status and breach history
- Detailed event history with filtering and sorting
- API endpoints for integration with other systems

## Project Structure

```
astra/
├── app/
│   ├── api/            # API endpoints
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   ├── templates/      # HTML templates
│   ├── utils/          # Utility functions
│   └── views/          # View functions
├── config/             # Configuration files
├── logs/               # Application logs
├── tests/              # Test files
└── requirements/       # Python dependencies
```

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

The application can be configured using environment variables or a `.env` file:

- `FLASK_ENV`: Environment (development/production)
- `DATABASE_URL`: Database connection URL
- `SECRET_KEY`: Application secret key
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)

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
