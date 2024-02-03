from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime

## Next Step is Login!!

# Just the basic setup stuff
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
login_manager = LoginManager()


# This is my DB Schema for added user added content.
class NewStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False) 
    genre = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return '<new_story %r>' % self.id


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
