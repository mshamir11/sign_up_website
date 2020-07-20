from flask import Flask,render_template,url_for,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///updates.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///updates.db'
db = SQLAlchemy(app)

class updates(db.Model):
    id    = db.Column(db.Integer,primary_key =True)
    title = db.Column(db.String(50))
    content = db.Column(db.Text)
    date_posted = db.Column(db.DateTime)
    



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








if __name__ == "__main__":
    app.run(debug=True)