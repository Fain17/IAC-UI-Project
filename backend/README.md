# IAC UI Agent

A FastAPI-based web application for managing EC2 instances and launch templates in AWS.

## Project Structure

```
iac_ui_agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration settings
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main_routes.py      # Web interface routes
│   │   └── api_routes.py       # API endpoints
│   └── services/
│       ├── __init__.py
│       ├── launch_template_service.py  # Launch template operations
│       └── mapping_service.py          # Configuration mapping operations
├── config/
│   └── mappings.json           # Instance to launch template mappings
└── requirements.txt
```

## Features

- Create AMI from EC2 instances
- Update launch templates with new AMIs
- Manage instance to launch template mappings
- Web interface and JSON API endpoints
- Secure input validation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials (via AWS CLI, environment variables, or IAM roles)

3. Run the application:
```bash
python -m app.main
```

## Usage

### Web Interface
- Visit `http://localhost:8000` for the main form
- Enter EC2 instance name tag and launch template name
- Submit to create AMI and update launch template

### API Endpoints

- `POST /api/run-json` - JSON endpoint for AMI creation
- `GET /api/get-all-mappings` - Get all instance mappings
- `POST /api/save-mapping` - Save new instance mapping
- `POST /api/delete-mapping` - Delete instance mapping

## Configuration

- Set `AWS_REGION` environment variable to specify AWS region
- Mappings are stored in `config/mappings.json`
- Application settings in `app/config/settings.py` 