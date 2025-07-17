import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# LibSQL Database Configuration
LIBSQL_URL = os.getenv("LIBSQL_URL", "file:./data/iac_ui_agent.db")
LIBSQL_AUTH_TOKEN = os.getenv("LIBSQL_AUTH_TOKEN", None)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Application settings
APP_NAME = "IAC UI Agent"
APP_VERSION = "1.0.0" 