from flask import Flask,render_template,url_for,request,redirect,flash,session,logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

#config mysql
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///updates.db'
app.secret_key = 'imsuperman'


db = SQLAlchemy(app)

class updates(db.Model):
    id    = db.Column(db.Integer,primary_key =True)
    title = db.Column(db.String(50))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime)
    
class users(db.Model):
    id = db.Column(db.Integer,primary_key =True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    username = db.Column(db.String(30))
    password = db.Column(db.String(30))
    register_date = db.Column(db.DateTime)
    
#WTF form for register
class RegisterForm(Form):
    name = StringField("Name",[validators.Length(min=1,max=50)])
    username = StringField("Username",[validators.Length(min=1,max=30)])
    email = StringField("Email",[validators.Length(min=6,max=50)])
    password = PasswordField("Password",[validators.DataRequired(),
    validators.EqualTo('confirm',message='Password do not match')])
    confirm = PasswordField('Confirm Password')

@app.route('/')
def home():
    posts = updates.query.all()
    
    return render_template("index.html",posts=posts)

@app.route('/add')
def add():
    return render_template("add.html")

@app.route('/addpost',methods=['POST'])
def addpost():
    title = request.form['title']
    minutes = request.form['minutes']
    
    post = updates(title=title,content = minutes,date_posted=datetime.now())
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('home'))


#Registeration route
@app.route('/register_alphamegazord',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(form.password.data)

        post_user = users(name=name,email=email,username = username,password =password,register_date=datetime.now())
        db.session.add(post_user)
        db.session.commit()

        flash("You are now registered and can log in","success")

        return redirect(url_for('home'))
    
    return render_template('register.html',form=form)


#user login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        app.logger.info(password_candidate)

        data = users.query.filter_by(username=username).first()
        if data:
            password = data.password
            app.logger.info(password)

            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] = True
                session['username'] = username

                flash(' You are now logged in','success')

                return redirect(url_for('dashboard'))
            
            else:
                # app.logger.info('PASSWORD NOT MATCHED')
                error ='Invalid password'
                return render_template('login.html',error=error)

        
        else:
            error ='User not found'
            return render_template('login.html',error=error)

    return render_template('login.html')

#Check if user is logged i


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash ("Unauthorized, Please Log in","danger")
            return redirect(url_for('login'))
    return wrap


@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out","success")
    return redirect(url_for('login'))


#Minutes form class

class ArticleForm(Form):
    title = StringField("title",[validators.Length(min=1,max=200)])
    body = TextAreaField('Body',[validators.Length(min=20)])

#Add articluep  
@app.route('/add_articles',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method =='POST' and form.validate():
        title = form.title.data
        body = form.body.data

        post_articles = updates(title=title,content=body,date_posted=datetime.now())
        db.session.add(post_articles)
        db.session.commit()

        flash('Article Created','success')

        return redirect(url_for('dashboard'))
    return render_template('add_articles.html',form=form)

if __name__ == "__main__":
    app.run(debug=True)