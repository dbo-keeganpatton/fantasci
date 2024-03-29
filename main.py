from flask import Flask, redirect, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.recaptcha import validators
from flask_migrate import Migrate
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import backref
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from datetime import datetime
from flask_bcrypt import Bcrypt
import json
import bleach
import traceback
import os

# Retrieve Auth Secret
# with open('secret.json', 'r') as file:
#    secret = json.load(file)

# Retrieve secret upon deployment
secret = os.getenv('secret')

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



#############################################################################################################################################
"""                                                         DATABASE SCHEMAS                                                              """
#############################################################################################################################################

migrate = Migrate(app, db)

""" 
Migrate for running Database Migrations when Schemas Change
run the following commands in terminal when this is neccesary
|--export FLASK_APP=main.py
||-- flask db init
|||-- flask db upgrade -m 'some message'
||||-- flask db upgrade
""" 

""" Database Notes """
# Deleting a story from the 'NewStory' class will remove all subsequent Versions and Merge Requests for that story.
# This is intended functionality until a more elegant solution is created.


###################################################
#               Core Story Entries                #
###################################################

class NewStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False) 
    genre = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_version_id = db.Column(db.Integer, db.ForeignKey('new_version.id'), nullable=True)

    # Relationships
    __table_args__ = (
        ForeignKeyConstraint(['author_id'], ['user.id'], name='fk_new_story_author_id'),
        ForeignKeyConstraint(['current_version_id'], ['new_version.id'], name='fk_new_story_current_version_id')
    )

    current_version = db.relationship('NewVersion', foreign_keys=[current_version_id], post_update=True)
    versions = db.relationship('NewVersion', backref='story', lazy=True, cascade='all, delete-orphan', foreign_keys='NewVersion.story_id')

    def __repr__(self):
        return '<new_story %r>' % self.id


class NewVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    story_id = db.Column(db.Integer, db.ForeignKey('new_story.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    __table_args__ = (
        ForeignKeyConstraint(['story_id'], ['new_story.id'], name='fk_new_version_story_id'),
        ForeignKeyConstraint(['author_id'], ['user.id'], name='fk_new_version_author_id')
    )
    
    author = db.relationship('User', backref='versions', foreign_keys=[author_id])
    
    def __repr__(self):
        return '<new_version %r>' % self.id


class MergingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('new_story.id'), nullable=False)
    version_id = db.Column(db.Integer, db.ForeignKey('new_version.id'), nullable=False) 
    requestor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    status = db.Column(db.String(20), default='Pending', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate = datetime.utcnow())

    # Relationships
    story = db.relationship('NewStory', backref=backref('merging_requests', cascade='all, delete', lazy=True))
    version = db.relationship('NewVersion', backref=backref('merging_requests', uselist=False))
    requestor = db.relationship('User', backref=backref('merging_requests', lazy=True))


###################################################
#               User Schemas                      #
###################################################

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    stories = db.relationship('NewStory', backref='author', lazy=True, foreign_keys=[NewStory.author_id])


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



#############################################################################################################################################
"""                                                             ROUTES                                                                    """
#############################################################################################################################################


###################################################
#                 Login Routes                    #
###################################################


@app.route('/register/', methods=['GET', 'POST'])
def register():
    '''First Time Register'''
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
    '''Central Login'''
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
    '''Landing Page / Mission Statement'''
    return render_template('index.html', current_user=current_user)



###################################################
#               Author Canvas GUI                 #
###################################################

@app.route('/writer/', methods=['GET', 'POST'])
def writer():
    '''GUI where users can Auther and contribute to Stories'''
    if request.method == 'POST':
        
        story_title = request.form['title']
        # Bleach is used here to clean allowable HTML tags for security.
        story_content = bleach.clean( 
            request.form['content'], tags=list(
                bleach.sanitizer.ALLOWED_TAGS
            ) + 
            [ 'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'ul', 'ol', 'li', 'blockquote' ], 
            strip=True
        )
        story_genre = request.form['genre']
        author_id = current_user.id
        add_story = NewStory(title=story_title, content=story_content, genre=story_genre, author_id=author_id)

        try:
            db.session.add(add_story)
            db.session.commit()
            return redirect('/story_db/')
        except Exception as e:
            db.session.rollback()
            flash("Something is Wrong..." + str(e))
            return redirect('/writer/')

    else:
        stories = NewStory.query.order_by(NewStory.date_created).all()
        return render_template('writer.html', stories=stories, current_user=current_user)



###################################################
#           Story Repo and Reading Routes         #
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

    return render_template('story_db.html', stories=stories, unique_genres=unique_genres, current_user=current_user)



@app.route('/read_version/<int:version_id>', methods=['GET'])
def read_version(version_id):
    '''Review Version from Version list'''
    version = NewVersion.query.get_or_404(version_id)
    story = version.story
    return render_template('read_version.html', version=version, story=story)



@app.route('/viewstory/<int:id>', methods=['GET'])
def view_story(id):
    '''Hyperlink to Select Story'''
    story = NewStory.query.get_or_404(id)
    return render_template('view_story.html', story=story, current_user=current_user)



###################################################
#                  CRUD actions                   #
###################################################


@app.route('/delete/<int:id>')
def delete(id):
    '''Delete Posts'''
    story_to_delete = NewStory.query.get_or_404(id)

   # try:
    db.session.delete(story_to_delete)
    db.session.commit()
    return redirect('/story_db/')
    #except:
     #   Exception 



@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    '''Update Post'''
    story = NewStory.query.get_or_404(id)
    if request.method == 'POST':
        
        new_version = NewVersion(
            content = request.form['content'],
            story_id = id,
            author_id = current_user.id 
        )

        try:
            db.session.add(new_version)
            db.session.commit()
            # Merge request functionality
            initiate_merge = request.form.get('initiate_merge_request') == 'true'
            if initiate_merge:
                merge_request = MergingRequest(
                    story_id=id,
                    version_id=new_version.id,
                    requestor_id=current_user.id,
                    status='Pending'
                )

                db.session.add(merge_request)
                db.session.commit()
            return redirect('/story_db/')
        
        except Exception as e:
            db.session.rollback()
            details = traceback.format_exc()
            print(details)
    else:
        return render_template('update.html', story=story, current_user=current_user)



###################################################
#               User Directory View               # 
###################################################

@app.route('/user_dir/', methods=['GET'])
def user_dir():
    '''List of Registered'''
    users_in_dir = User.query.join(NewStory, User.id == NewStory.author_id).all()
    return  render_template('user_dir.html', users=users_in_dir)



@app.route('/user_dir_stories/<int:user_id>/', methods=['GET'])
def user_dir_stories(user_id):
    '''stories users wrote'''
    user = User.query.get_or_404(user_id)
    stories = NewStory.query.filter_by(author_id=user_id).all()
    return  render_template('user_dir_stories.html', user=user, stories=stories)



###################################################
#           Version Control System Routes         # 
###################################################

@app.route('/versions/<int:id>', methods=['GET'])
def versions(id):
    '''Version History for Changes to a Story'''
    story = NewStory.query.get_or_404(id)
    versions = NewVersion.query.filter_by(story_id=id).order_by(NewVersion.date_created.desc()).all()
    return render_template('versions.html', story=story, versions=versions, current_user=current_user)



@app.route('/merge_requests/', methods=['GET'])
@login_required
def view_merge_requests():
    '''Show User PR Req'''
    merge_requests = MergingRequest.query.join( NewStory, MergingRequest.story_id == NewStory.id).filter(
        NewStory.author_id == current_user.id,
        MergingRequest.status == "Pending").all()
    return render_template('merge_requests.html', merge_requests=merge_requests)



# This route is slightly more complicated.
@app.route('/review_changes/<int:version_id>', methods=['GET', 'POST'])
def review_changes(version_id):
    '''Review Merge Req Version'''
    # Retrieve version to replace original.
    version = NewVersion.query.get_or_404(version_id)
    story = version.story
    
    if request.method == "POST":
        # The HTML template uses "action" buttons with corresponding aliases.
        # Get the merge request ID so we can delete it after it has been seen and approved or denied.
        action = request.form.get('action')
        merging_requests = MergingRequest.query.filter_by(version_id=version.id).first()

        if action == "Accept Changes":
            story.content = version.content 
        elif action == "Deny Changes":
            flash("Merge Denied", "Info")
        if merging_requests:
            db.session.delete(merging_requests)
            db.session.commit()
        return redirect('/merge_requests/')
    return render_template('review_changes.html', version=version, story=story)



###################################################
#                     END APP                     # 
###################################################

# add with app.app_context(): db.create_all() if needed.
if __name__ == "__main__":
    app.run()
