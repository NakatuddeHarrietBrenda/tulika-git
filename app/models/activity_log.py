from app import db
from datetime import datetime

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f"<ActivityLog {self.user_email} - {self.action} at {self.timestamp}>"
