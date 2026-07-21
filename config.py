"""
GLS Bug Bounty Platform

Copyright (C) 2026 Dhiptanshu Malik

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See the LICENSE file for details.
"""
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
