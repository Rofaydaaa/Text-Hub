from datetime import datetime
from texthub import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    token_fb = db.Column(db.String(60), nullable=True)
    page_id_fb = db.Column(db.String(60), nullable=True)
    consumer_key_twitter = db.Column(db.String(60), nullable=True)
    consumer_secret_twitter = db.Column(db.String(60), nullable=True)
    access_token_twitter = db.Column(db.String(60), nullable=True)
    access_secret_twitter = db.Column(db.String(60), nullable=True)

    posts = db.relationship('Posts', backref='author', lazy=True, order_by="desc(Posts.date_posted)")
    archive_posts = db.relationship('ArchivePosts', backref='author', lazy=True, order_by="desc(ArchivePosts.date_archived)")
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title =  db.Column(db.String(255))
    body = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow)
    posted_on_fb = db.Column(db.Boolean, default=False)
    posted_on_twitter = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
    
class ArchivePosts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title =  db.Column(db.String(255))
    body = db.Column(db.Text)
    date_archived = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_archived}')"
    

class FacebookPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    platform_post_id = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f"FacebookPost('{self.fb_post_id}')"


class TwitterPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    platform_post_id = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f"TwitterPost('{self.twitter_post_id}')"
    
