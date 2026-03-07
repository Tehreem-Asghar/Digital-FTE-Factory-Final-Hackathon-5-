# conftest.py
"""Shared fixtures for Stage 3 E2E test suite."""
import os
import sys

# Ensure project root is on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set test environment variables
os.environ.setdefault("DATABASE_URL", "postgresql://fte_user:fte_password@localhost:5433/fte_db")
os.environ.setdefault("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "saasflow_verify_token")
os.environ.setdefault("ENVIRONMENT", "test")
