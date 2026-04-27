from flask_sqlalchemy import SQLAlchemy
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.Date, default=date.today)
    
    avatar = db.Column(db.String(200), default='/static/avatars/default-avatar.png')
    currency = db.Column(db.String(3), default='RUB')
    notifications_enabled = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)
    next_payment_date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.Date, default=date.today)
    
    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True))
    
    def __repr__(self):
        return f'<Subscription {self.name}>'