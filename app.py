from flask import Flask,render_template,url_for,request,redirect,flash,session,logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

#config mysql
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///updates.db'
app.secret_key = 'imsuperman'

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='1005730274054-3kp9tn3bc3shjchcqi6vk4kjgr5e6u62.apps.googleusercontent.com',
    client_secret='D_0y5xKgQS38IuxCZ3qZbTHH',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

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

    minutes = updates.query.all()
    if minutes:
        return render_template('dashboard.html',minutes=minutes)
    else:
        msg = "No articles found"
        return render_template('dashboard.html',msg=msg)


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

@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):

    #Get article by id
    result = updates.query.filter_by(id=id).first()
    #Get the form
    form = ArticleForm(request.form)

    #Populate article form fields

    form.title.data = result.title
    form.body.data = result.content
    

    if request.method =='POST' and form.validate():
        new_title = form.title.data
        new_body = form.body.data

        
        result.title = new_title
        result.content = new_body
        db.session.commit()

        flash('Article Updated','success')

        return redirect(url_for('dashboard')) 

    return render_template('edit_article.html',form=form)



@app.route('/google_login')
def google_login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize',_external=True)
    return google.authorize_redirect(redirect_uri)



@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed  to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    session['email'] = user_info['email']
    if user_info['verified_email']:
        session['logged_in'] = True
        flash("You are now logged In","success")
     # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # make the session permanant so it keeps existing after broweser gets closed
    return redirect('/')



if __name__ == "__main__":
    app.run(debug=True)