from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.recaptcha import validators
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from datetime import datetime
from flask_bcrypt import Bcrypt
import json

# Retrieve Auth Secret
with open('secret.json', 'r') as file:
    secret = json.load(file)

# Just the basic setup stuff
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = secret
db = SQLAlchemy(app)
login_manager = LoginManager()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

###################################################
#               Database Schemas                  #
###################################################


class NewStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False) 
    genre = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return '<new_story %r>' % self.id


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder" : "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder" : "Password"})
    submit = SubmitField("Register")
    
    def validate_username(self, username):
        '''Restrict Usernames to only Unique'''
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("Username Exists, try again..")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder" : "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder" : "Password"})
    submit = SubmitField("Login")
 


###################################################
#                 Login Routes                    #
###################################################



@app.route('/register/', methods=['GET', 'POST'])
def register():
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect('/')

    return render_template('register.html', form=form)



@app.route('/login/', methods=['GET', 'POST'])
def login():
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect('/')

    return render_template('login.html', form=form)


@app.route('/logout/', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')


###################################################
#           Landing/Content Creation Page         #
###################################################

@app.route('/', methods=['GET', 'POST'])
def index():
    '''Initialize Story Posts'''

    if request.method == 'POST':
        
        story_title = request.form['title']
        story_content = request.form['content']
        story_genre = request.form['genre']
        add_story = NewStory(title=story_title, content=story_content, genre=story_genre)

        try:
            db.session.add(add_story)
            db.session.commit()
            return redirect('/story_db/')
        except:
            "Something is Wrong..."

    else:
        stories = NewStory.query.order_by(NewStory.date_created).all()
        return render_template('index.html', stories=stories)


###################################################
#           Story Repo and CRUD actions           #
###################################################

@app.route('/story_db/', methods=['GET', 'POST'])
def story_db():
    '''View Created Stories'''
    
    stories = NewStory.query.order_by(NewStory.date_created).all()
    
    #### This helps create a genre dropdown filter for the db template ####
    unique_genres = set(story.genre for story in stories)
    if request.method == "POST":
        select_genre = request.form.get('Genre')
        if select_genre and select_genre != 'ALL':
            stories = [story for story in stories if story.genre == select_genre]


    return render_template('story_db.html', stories=stories, unique_genres=unique_genres)


@app.route('/delete/<int:id>')
def delete(id):
    '''Delete Posts'''

    story_to_delete = NewStory.query.get_or_404(id)

    try:
        db.session.delete(story_to_delete)
        db.session.commit()
        return redirect('/story_db/')
    except:
        "Something is Wrong..."


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    '''Update Post'''

    story = NewStory.query.get_or_404(id)

    if request.method == 'POST':
        story.title = request.form['title']
        story.genre = request.form['genre']
        story.content = request.form['content']
        
        try:
            db.session.commit()
            return redirect('/story_db/')
        except:
            "Something is wrong..."
   
    else:
        return render_template('update.html', story=story)


@app.route('/viewstory/<int:id>', methods=['GET'])
def view_story(id):
    '''Hyperlink to Select Story'''
    
    story = NewStory.query.get_or_404(id)
    return render_template('view_story.html', story=story)


###################################################
#                     END APP                     # 
###################################################

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
