import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-this-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ctf.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # The shared password for all participants to register/login
    GLOBAL_EVENT_PASSWORD = os.environ.get('EVENT_PASSWORD') or 'CYBERSHADEZ000'
    
    # Admin credentials (in a real scenario, manage via environment variables)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin_secret_pass'
