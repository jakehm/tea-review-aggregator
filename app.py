from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from PIL import Image
import uuid
from flask_migrate import Migrate

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "tea_reviews.db")}')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        # Generate a unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        
        # Open and resize image
        image = Image.open(file)
        # Maintain aspect ratio
        max_size = (800, 800)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # Save the processed image
        image.save(filepath, quality=85, optimize=True)
        
        return new_filename
    return None

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reviews = db.relationship('TeaReview', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Tea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vendor = db.Column(db.String(100), nullable=False, default='Unknown')
    producer = db.Column(db.String(100), nullable=False, default='Unknown')
    tea_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviews = db.relationship('TeaReview', backref='tea', lazy=True)
    
    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)

class TeaReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tea_id = db.Column(db.Integer, db.ForeignKey('tea.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    price = db.Column(db.String(100), nullable=True)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    review_id = db.Column(db.Integer, db.ForeignKey('tea_review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    review = db.relationship('TeaReview', backref=db.backref('comments', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    teas = Tea.query.order_by(Tea.created_at.desc()).all()
    return render_template('index.html', teas=teas)

@app.route('/search_tea')
def search_tea():
    query = request.args.get('query', '')
    teas = Tea.query.filter(
        (Tea.name.ilike(f'%{query}%')) |
        (Tea.vendor.ilike(f'%{query}%')) |
        (Tea.producer.ilike(f'%{query}%'))
    ).all()
    
    return jsonify([{
        'id': tea.id,
        'name': tea.name,
        'vendor': tea.vendor,
        'producer': tea.producer,
        'tea_type': tea.tea_type,
        'average_rating': tea.average_rating,
        'review_count': len(tea.reviews)
    } for tea in teas])

@app.route('/add_tea', methods=['POST'])
@login_required
def add_tea():
    name = request.form['tea_name']
    vendor = request.form['vendor']
    producer = request.form['producer']
    tea_type = request.form['tea_type']
    rating = int(request.form['rating'])
    review_text = request.form['review']
    price = request.form.get('price', '')  # Make price optional
    
    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            image_filename = save_image(file)
    
    # Check if tea already exists
    tea = Tea.query.filter_by(name=name, vendor=vendor, producer=producer).first()
    if not tea:
        # Create new tea
        tea = Tea(name=name, vendor=vendor, producer=producer, tea_type=tea_type)
        db.session.add(tea)
        db.session.commit()
    
    # Create the review
    new_review = TeaReview(
        rating=rating,
        review=review_text,
        price=price,
        image_filename=image_filename,
        user_id=current_user.id,
        tea_id=tea.id
    )
    db.session.add(new_review)
    db.session.commit()
    
    return redirect(url_for('view_tea', tea_id=tea.id))

@app.route('/tea/<int:tea_id>')
def view_tea(tea_id):
    tea = Tea.query.get_or_404(tea_id)
    reviews = TeaReview.query.filter_by(tea_id=tea_id).order_by(TeaReview.created_at.desc()).all()
    return render_template('tea_detail.html', tea=tea, reviews=reviews)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/my_reviews')
@login_required
def my_reviews():
    reviews = TeaReview.query.filter_by(user_id=current_user.id).order_by(TeaReview.created_at.desc()).all()
    return render_template('my_reviews.html', reviews=reviews)

@app.route('/add_comment/<int:review_id>', methods=['POST'])
@login_required
def add_comment(review_id):
    review = TeaReview.query.get_or_404(review_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty')
        return redirect(url_for('view_tea', tea_id=review.tea.id))
    
    comment = Comment(
        content=content,
        review_id=review_id,
        user_id=current_user.id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully')
    return redirect(url_for('view_tea', tea_id=review.tea.id))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
