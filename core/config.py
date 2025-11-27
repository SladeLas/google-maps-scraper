"""Configuration settings for the Dustly application."""
from environs import Env

env = Env()
env.read_env()

ENVIRONMENT = env.str("ENVIRONMENT", "development")
LOG_LEVEL = env.str("LOG_LEVEL", "INFO")
API_VERSION = "v1"

# Database
DB_URL = env.str("DB_URL", "postgresql://dustly:password@localhost/dustly")
DB_URI = env.str("DB_URI")
DB_HOST = env.str("DB_HOST")
DB_NAME = env.str("DB_NAME")
DB_USER = env.str("DB_USER")
DB_PASSWORD = env.str("DB_PASSWORD")
DB_PORT = env.str("DB_PORT")