import csv
from app import app, db
from models import User

def import_users():
    with app.app_context():
        # Re-create tables to add the new password column if it doesn't exist (simplest way for dev)
        # However, to preserve data, we might just want to add the column or rely on migration.
        # Given previous resets, I will just create everything if missing, but since we modify model, 
        # we might need to drop user table or alter it.
        # Let's try to add users. If column missing error, we might need to reset DB.
        # User explicitly asked to "Take username and mobile from CSV", implying new data.
        
        csv_path = 'Users (13).csv'
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    username = row['Username'].strip()
                    password = row['Mobile Number'].strip() # Password is Mobile Number
                    
                    if not username or not password:
                        continue
                        
                    # Check if user exists
                    existing_user = User.query.filter_by(username=username).first()
                    if existing_user:
                        print(f"Skipping {username} (already exists)")
                        continue
                    
                    new_user = User(username=username, password=password)
                    db.session.add(new_user)
                    count += 1
                
                db.session.commit()
                print(f"Successfully imported {count} users.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    import_users()
