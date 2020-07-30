from flask import Flask, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy, request
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime

# config params from config.json
local_server = True
with open("config.json", "r") as c:
    params = json.load(c)["params"]


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['upload_folder'] = params['upload_location']
# super key
app.secret_key = "super-secret-key"
# sending mail
app.config.update(

    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']


)
mail = Mail(app)
# database connection
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


# contact database
class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_no = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(120), nullable=True)


# Posts database
class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()[0:params["no_of_posts"]]
    return render_template('index.html', params=params, posts=posts)


@app.route('/uploader', methods=["GET", "POST"])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == "POST":
            f = request.files['file']
            f.save(os.path.join(app.config['upload_folder'], secure_filename(f.filename)))
            return "uploaded successfully"


@app.route('/logout')
def logout_user():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>', methods=["GET", "POST"])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    """
    Admin login to dashboard via user name password
    two condition define here 1.if user already login  win credential
    2.if user want to login in dashboard with username and password
    """

    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    else:
        return render_template('login.html', params=params)


@app.route('/edit/<string:sno>', methods=["GET", "POST"])
def edit(sno):

    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == "POST":
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, tagline=tline, slug=slug, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect(f'/edit/ {sno}')
    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, sno=sno, post=post)

    
@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route("/post/<string:post_slug>", methods=["GET"])
def post_route(post_slug):

    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route('/contact', methods=["GET", "POST"])
def contact():
    """
    user contact save in database after fill form in contact page
    admin get email of user info
    """
    if request.method == "POST":

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name, phone_no=phone, date=datetime.now(), email=email, msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message(
            f"New Mail From Blog {name}",
            sender=email,
            recipients=[params['gmail_user']],
            body=f"{message} \n {phone}"

        )
    return render_template('contact.html', params=params)


app.run(debug=True)
