from app import create_app, db
from models.user import User
import os

app = create_app()

with app.app_context():
    db.create_all()
    
    # Create default admin if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@platform.ai', role='Admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin / admin123")
    else:
        print("Admin already exists.")
