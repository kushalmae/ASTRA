# ASTRA - Automated Satellite Threshold Reporting & Alerts

A scalable, configuration-driven web application that monitors MATLAB-based metrics for a constellation of satellite payloads. When thresholds are breached, the system logs the events in a database and displays real-time insights through a Flask-based dashboard.

## Features

- Configuration-driven architecture - easily add new metrics and thresholds
- Real-time monitoring of metrics for 10 satellite payloads
- Dashboard with visual indicators of breaches
- Detailed event table with filtering and sorting capabilities
- SQLite database for persistent storage
- Simulated MATLAB integration (can be replaced with actual MATLAB scripts)

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/ASTRA.git
cd ASTRA
```

2. Create a virtual environment and activate it:
```
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

## Configuration

The application is configured through the `config/metrics_config.json` file. This file defines the metrics and thresholds for monitoring. 

Example:
```json
{
  "metrics": {
    "thermal": {"threshold": 75.0},
    "voltage": {"threshold": 3.3},
    "latency": {"threshold": 250}
  },
  "payloads": [
    {"scid": 101, "name": "Payload 1"},
    {"scid": 102, "name": "Payload 2"},
    ...
  ]
}
```

### Environment Variables

The application can be configured using environment variables or an `.env` file. Copy `env.example` to `.env` and modify as needed:

```
# Path to MATLAB scripts folder
MATLAB_SCRIPTS_PATH=./matlab_scripts

# Refresh interval for monitoring, in seconds
REFRESH_INTERVAL=600

# Database path
DATABASE_PATH=./data/astra.db

# Use simulation mode instead of real MATLAB
USE_SIMULATION=True
```

Setting `USE_SIMULATION=True` will use the built-in simulator instead of trying to run real MATLAB scripts.

## Running the Application

Simply run:
```
python app.py
```

The application will start a Flask web server on http://localhost:5000 and a background thread that simulates MATLAB script execution at regular intervals.

## MATLAB Integration

The current implementation simulates MATLAB script execution for testing purposes. To integrate with actual MATLAB scripts:

1. Place your MATLAB scripts in the `matlab_scripts` directory
2. Update the `app/matlab_interface.py` file to call your scripts using the MATLAB Engine API or `subprocess`

## Project Structure

- `app/` - Main application package
  - `__init__.py` - Flask application initialization
  - `config.py` - Configuration handling
  - `database.py` - Database operations
  - `matlab_interface.py` - MATLAB script interface
  - `routes.py` - Flask routes for the web interface
  - `static/` - Static files (CSS, JS)
  - `templates/` - Jinja2 templates
- `config/` - Configuration files
- `data/` - Database files
- `matlab_scripts/` - MATLAB scripts
- `app.py` - Application entry point

## Troubleshooting

### SQLite Threading Issues

The application is designed to handle SQLite's thread safety requirements. Each thread (main Flask thread, background monitoring thread, and request handling threads) has its own dedicated database connection to avoid the "SQLite objects created in a thread can only be used in that same thread" error.

### MATLAB Integration Issues

If you encounter issues with MATLAB integration:

1. Make sure MATLAB is installed and accessible from the command line
2. Verify the MATLAB scripts in the `matlab_scripts` directory are working correctly
3. Try setting `USE_SIMULATION=True` in your `.env` file to bypass MATLAB and use simulated data
