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
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = float(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "1"))  # 1 day

# Cleanup Configuration
CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "60"))  # 1 minute for testing

# Application settings
APP_NAME = "IAC UI Agent"
APP_VERSION = "1.0.0" 