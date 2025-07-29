from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, redirect, url_for, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.sql import func

app = Flask(__name__)

# DB for Keystone web-site
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keystone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # нужно для сессий

db = SQLAlchemy(app)

# Models
class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Page(db.Model):
    __tablename__ = 'pages'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class ContentBlock(db.Model):
    __tablename__ = 'content_blocks'

    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id', ondelete='CASCADE'), nullable=False)
    identifier = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Servant(db.Model):
    __tablename__ = 'servants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=False, unique=True)
    role = db.Column(db.String(255), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Parishioner(db.Model):
    __tablename__ = 'parishioners'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    surname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=False, unique=True)
    birth_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    servant_id = db.Column(db.Integer, db.ForeignKey('servants.id', ondelete='CASCADE'), nullable=False)
    parishioner_id = db.Column(db.Integer, db.ForeignKey('parishioners.id', ondelete='CASCADE'), nullable=False)


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    servant_id = db.Column(db.Integer, db.ForeignKey('servants.id', ondelete='CASCADE'), nullable=False)
    parishioner_id = db.Column(db.Integer, db.ForeignKey('parishioners.id', ondelete='CASCADE'), nullable=False)


with app.app_context():
    db.create_all()
    print("DB and tables succesfully created!")


# admin panel 

# API Routes

@app.route('/home')
def home():
    return 'Простой CRUD на Flask и SQLAlchemy!'

@app.route('/')
def index():
    return render_template('index.html')   

# API CRUD

@app.route('/admin_add', methods=['GET', 'POST'])
def admin_add():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        admin = Admin(login=login)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('admin_add.html', action='Create') 
        

@app.route('/admin_list', methods=['GET'])
def admin_list():
    admins = Admin.query.all()
    return render_template('admin_list.html', admins=admins)

@app.route('/admin_detail/<int:id>', methods=['GET'])
def admin_detail(id):
    admin = Admin.query.get_or_404(id) 
    return render_template('admin_detail.html', admin=admin)    

@app.route('/admin_edit/<int:id>', methods=['GET', 'POST'])
def admin_edit(id):
    admin = Admin.query.get_or_404(id)
    if request.method == 'POST':
        admin.login = request.form['login']
        password = request.form['password']
        if password:
            admin.set_password(password)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('admin_edit.html', admin=admin, action='Edit')

@app.route('/admin_delete/<int:id>') 
def admin_delete(id):
    admin = Admin.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    return redirect(url_for('index'))      


@app.route('/page_create', methods=['GET', 'POST'])
def page_create():
    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        page = Page(title=title, slug=slug)
        db.session.add(page)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('page_create.html', action='Create')

@app.route('/page_list', methods=['GET'])
def page_list():   
    pages = Page.query.all()
    return render_template('page_list.html', pages=pages)

@app.route('/page_detail/<slug>', methods=['GET'])
def page_detail(slug):   
    page = Page.query.filter_by(slug=slug).first_or_404()
    return render_template('page_detail.html', page=page) 

@app.route('/page_edit/<slug>', methods=['GET','POST'])
def page_edit(slug):
    page = Page.query.filter_by(slug=slug).first_or_404()
    if request.method == 'POST':
        page.title = request.form['title']
        page.slug = request.form['slug']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('page_edit.html', page=page, action='Edit')

@app.route('/page_delete/<slug>')
def page_delete(slug):
    page = Page.query.filter_by(slug=slug).first_or_404()
    db.session.delete(page)
    db.session.commit()
    return redirect(url_for('index'))        


# entry point
if __name__ == '__main__':
    app.run(debug=True)
