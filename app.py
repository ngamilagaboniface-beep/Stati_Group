import os
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'STATI_GROUP_PREMIUM_2026')

# Cloudinary Setup for Image Uploads
cloudinary.config(
  cloud_name = os.environ.get('CLOUDINARY_NAME'),
  api_key = os.environ.get('CLOUDINARY_API_KEY'),
  api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'stati_group.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_type = db.Column(db.String(50)) 
    location = db.Column(db.String(100)) 
    title = db.Column(db.String(150))
    price = db.Column(db.Float)
    features = db.Column(db.String(200)) 
    image_url = db.Column(db.String(500))

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100))
    client_phone = db.Column(db.String(20))
    message = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(id): 
    return User.query.get(int(id))

# --- INITIALIZATION ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='stati_admin'))
        db.session.commit()

# --- PUBLIC ROUTES ---
@app.route('/')
def index():
    search_loc = request.args.get('location')
    search_type = request.args.get('type')
    
    query = Property.query
    if search_loc: query = query.filter(Property.location.contains(search_loc))
    if search_type: query = query.filter(Property.property_type == search_type)
    
    properties = query.order_by(Property.id.desc()).all()
    return render_template('index.html', properties=properties)

@app.route('/contact', methods=['POST'])
def contact():
    new_inq = Inquiry(
        client_name=request.form.get('name'),
        client_phone=request.form.get('phone'),
        message=request.form.get('message')
    )
    db.session.add(new_inq)
    db.session.commit()
    flash('Thank you for contacting Stati Group. Our agent will call you shortly.')
    return redirect(url_for('index'))

# --- ADMIN & AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    properties = Property.query.order_by(Property.id.desc()).all()
    inquiries = Inquiry.query.order_by(Inquiry.date_created.desc()).all()
    return render_template('admin.html', properties=properties, inquiries=inquiries)

@app.route('/admin/upload', methods=['POST'])
@login_required
def upload_property():
    file = request.files['file']
    # Upload picture to Cloudinary
    upload_result = cloudinary.uploader.upload(file)
    
    new_prop = Property(
        title=request.form.get('title'),
        location=request.form.get('location'),
        property_type=request.form.get('type'),
        price=float(request.form.get('price')),
        features=request.form.get('features'),
        image_url=upload_result['secure_url']
    )
    db.session.add(new_prop)
    db.session.commit()
    flash('New property successfully listed!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
def delete_property(id):
    prop = Property.query.get_or_404(id)
    db.session.delete(prop)
    db.session.commit()
    flash('Property removed from the public listing.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/change_password', methods=['POST'])
@login_required
def change_password():
    old_pw = request.form.get('old_password')
    new_pw = request.form.get('new_password')
    
    if current_user.password == old_pw:
        current_user.password = new_pw
        db.session.commit()
        flash('Admin password successfully updated.')
    else:
        flash('Incorrect current password.')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
