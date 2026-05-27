from app import app, db
from models import User

with app.app_context():
    username = "CYBERSHADEZTEST"
    password = "1234567890" # Dummy mobile for testing
    
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"User {username} already exists. Updating password.")
        user.password = password
    else:
        print(f"Creating user {username}.")
        user = User(username=username, password=password)
        db.session.add(user)
    
    db.session.commit()
    print(f"Test User Ready:\nUsername: {username}\nPassword: {password}")
