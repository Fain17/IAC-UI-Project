import os
from pathlib import Path
from typing import Optional

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# Application Configuration
APP_NAME = "IAC UI Agent"
APP_VERSION = "1.0.0"

# Database Configuration
LIBSQL_URL = os.getenv("LIBSQL_URL", "file:data/database.db")
LIBSQL_AUTH_TOKEN = os.getenv("LIBSQL_AUTH_TOKEN", "")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # 30 minutes for testing
REFRESH_TOKEN_EXPIRE_DAYS = float(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 7 days

# Cleanup Configuration
CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "3600"))  # 1 hour 