import os
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'STATI_GROUP_SECURE_2026'

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'stati_group.db')
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    location = db.Column(db.String(100))
    price = db.Column(db.Float)
    image_url = db.Column(db.String(500))

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    selected_plots = db.Column(db.Text) # Stores names of plots from cart
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='2007fe'))
        db.session.commit()

# --- ROUTES ---
@app.route('/')
def index():
    properties = Property.query.all()
    return render_template('index.html', properties=properties)

@app.route('/send_inquiry', methods=['POST'])
def send_inquiry():
    new_inquiry = Inquiry(
        customer_name=request.form.get('name'),
        customer_email=request.form.get('email'),
        customer_phone=request.form.get('phone'),
        selected_plots=request.form.get('cart_data')
    )
    db.session.add(new_inquiry)
    db.session.commit()
    flash('Asante! Your inquiry for the selected plots has been sent.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
