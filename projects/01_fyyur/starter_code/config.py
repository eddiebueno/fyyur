import os

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_TRACK_MODIFICATIONS = False

# IMPLEMENT DATABASE URL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}:{}/{}".format(
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
)
