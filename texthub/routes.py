from flask import render_template, url_for, flash, redirect, request
from flask_restx import Api, Resource
from texthub import app, db, bcrypt
from texthub.forms import RegistrationForm, LoginForm, PostForm, UpdateAccountForm, UpdatePlatforms
from texthub.models import User, Posts, ArchivePosts, FacebookPost, TwitterPost
from flask_login import login_user, current_user, logout_user, login_required
import requests, tweepy
from datetime import datetime

# Sample resource for Swagger documentation
# @api.route('/sample')
# class SampleResource(Resource):
#     def get(self):
#         """Sample endpoint"""
#    
#      return {'message': 'Hello, Swagger!'}

def update_user_account(form):
    current_user.username = form.username.data
    current_user.email = form.email.data
    db.session.commit()

def update_platforms(form):
    success = True

    if not form.select_fb.data:
        form.reset_fb_fields()
    elif form.form_fb_fields_are_valid():
        form.set_fb_fields()
    else:
        success = False
        form.reset_fb_fields()
        flash(f'Adding platform failed, enter your facebook page access token', 'danger')

    if not form.select_twitter.data:
        form.reset_twitter_fields()
    elif form.form_twitter_fields_are_valid():
        form.set_twitter_fields()
    else:
        success = False
        form.reset_twitter_fields()
        flash(f'Adding platform failed, enter all twitter fields', 'danger')

    db.session.commit()

    if success:
        flash(f'Platforms have been updated', 'success')

def post_fb(post):
    access_token = current_user.token_fb
    page_id = current_user.page_id_fb
    url = f'https://graph.facebook.com/v18.0/{page_id}/feed'
    data = {'access_token': access_token, 'message': post}

    r = requests.post(url, data=data)
    return r.json()['id']

def post_twitter(tweet):
    client = tweepy.Client(
         consumer_key=current_user.consumer_key_twitter, consumer_secret=current_user.consumer_secret_twitter,
         access_token=current_user.access_token_twitter, access_token_secret=current_user.access_secret_twitter
     )

    response = client.create_tweet(text=tweet)
    return response.data['id']

def delete_fb(id):
    access_token = current_user.token_fb

    url = f'https://graph.facebook.com/v18.0/{id}'
    data = {'access_token': access_token}

    requests.delete(url, params=data)

def delete_twitter(id):
    client = tweepy.Client(
         consumer_key=current_user.consumer_key_twitter, consumer_secret=current_user.consumer_secret_twitter,
         access_token=current_user.access_token_twitter, access_token_secret=current_user.access_secret_twitter
     )

    client.delete_tweet(id)

def update_fb(id, form):
    pass

def update_twitter(id, form):
    pass

platforms = ['fb', 'twitter']

platform_post_functions = {
    'fb': post_fb,
    'twitter': post_twitter,
}

platform_delete_functions = {
    'fb': delete_fb,
    'twitter': delete_twitter,
}

platform_update_functions = {
    'fb': update_fb,
    'twitter': update_twitter,
}

PLATFORM_MODELS = {
    'fb': FacebookPost,
    'twitter': TwitterPost,
}

@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html', title='Home')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login",  methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password ,form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash(f'Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form_name = UpdateAccountForm()
    form_platform = UpdatePlatforms()

    if form_name.validate_on_submit():
        update_user_account(form_name)
        flash(f'Your account has been updated', 'success')
        return redirect(url_for('profile'))
    
    if form_platform.validate_on_submit():
        update_platforms(form_platform)
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        form_name.populate_forms_with_user_data()
        form_platform.populate_forms_with_user_data()
        
    return render_template('profile.html', title='Profile', form_name=form_name, form_platform=form_platform)

@app.route("/editor/<int:post_id>", methods=['GET', 'POST'])
@app.route("/editor", methods=['GET', 'POST'])
@login_required
def editor(post_id=None):

    form = PostForm()

    archived = request.args.get('archived', default=False, type=bool)
    edited = request.args.get('edited', default=False, type=bool)

    if form.validate_on_submit():
        if form.submit.data:
            # Check for Edit Mode
            if not edited:
                success = True
                selected_platforms = []
                post_ids = {}
                for platform in platforms:
                    select_field = getattr(form, f'select_{platform}')

                    if select_field.data:
                        selected_platforms.append(platform)
                        tokens_available = getattr(form, f'{platform}_tokens_available')
                        validation_function = getattr(form, f'{platform}_tokens_validation')

                        if not tokens_available() or not validation_function():
                            success = False
                if not selected_platforms:
                    flash('Please select at least one platform, or add it to archive and post it later', 'danger')
                    success = False

                if success:
                    post = Posts(
                        title=form.title.data,
                        body=form.body.data,
                        posted_on_fb=form.select_fb.data,
                        posted_on_twitter=form.select_twitter.data,
                        user_id=current_user.id
                    )
                    message = form.title.data + "\n" + form.body.data
                    for platform in selected_platforms:
                        post_ids[platform] = platform_post_functions[platform](message)

                    db.session.add(post)
                    db.session.commit()

                    for platform in selected_platforms:
                        platform_model = PLATFORM_MODELS[platform]
                        platform_post = platform_model(
                            original_post_id=post.id,
                            platform_post_id=post_ids[platform]
                        )
                        db.session.add(platform_post)

                    db.session.commit()

                    flash(f'Posted successfully', 'success')
                    return redirect(url_for('editor'))
            else:
                success, update_platforms = can_update_or_delete(post_id)
                if success:
                    for platform in update_platforms:
                        platform_model = PLATFORM_MODELS[platform]
                        platform_post = platform_model.query.filter_by(original_post_id=post_id).first()   
                        #uncomment this line when updeate functions are supporetd
                        #platform_update_functions[platform](platform_post.platform_post_id, form)
                    post = Posts.query.get_or_404(post_id)
                    post.title = form.title.data
                    post.body = form.body.data
                    post.date_updated = datetime.utcnow()
                    db.session.commit()
                    flash(f'Updated successfully on our app only, not reflected on your platforms, updating feature is not supported now on your selected platforms', 'success')
                    return redirect(url_for('editor'))
        elif form.archive.data:
            if not edited:
                post = ArchivePosts(
                        title=form.title.data,
                        body=form.body.data,
                        user_id=current_user.id
                    )
                db.session.add(post)
            else:
                post = ArchivePosts.query.get_or_404(post_id)
                post.title = form.title.data
                post.body = form.body.data
                post.date_archived = datetime.utcnow()
            db.session.commit()
            flash(f'Added to archive successfully', 'success')
            return redirect(url_for('editor'))

    # Filling form in case of update    
    if archived:
        post = ArchivePosts.query.get_or_404(post_id)
        form.title.data = post.title
        form.body.data = post.body
    # If post_id is provided, fetch the post from the database
    if post_id is not None and not archived and edited:
        post = Posts.query.get_or_404(post_id)
        form.title.data = post.title
        form.body.data = post.body
        form.select_fb.data = post.posted_on_fb
        form.select_twitter.data = post.posted_on_twitter
        return render_template('editor.html', title='Editor', form=form, edit_mode=True, post_id=post_id)
    return render_template('editor.html', title='Editor', form=form, edit_mode=False)

@app.route("/posts", methods=['GET', 'POST'])
@login_required
def posts():

    all_posts = current_user.posts
    archive_posts = current_user.archive_posts
    fb_posts = Posts.query.filter_by(user_id=current_user.id, posted_on_fb=True).order_by(Posts.date_posted.desc()).all()
    twitter_posts = Posts.query.filter_by(user_id=current_user.id, posted_on_twitter=True).order_by(Posts.date_posted.desc()).all()

    return render_template("posts.html", all_posts=all_posts, archive_posts=archive_posts, fb_posts=fb_posts, twitter_posts=twitter_posts)

@app.route("/delete_post", methods=['POST'])
@login_required
def delete_post():

    post_id = request.form['post_id']
    post_type = request.form['post_type']

    if post_type == 'post':
        post = Posts.query.get_or_404(post_id)

        success, deleted_platforms = can_update_or_delete(post_id)
        
        if success: 
            for platform in deleted_platforms:
                platform_model = PLATFORM_MODELS[platform]
                platform_post = platform_model.query.filter_by(original_post_id=post_id).first()   
                platform_delete_functions[platform](platform_post.platform_post_id)
                db.session.delete(platform_post)
        else:
            flash('An error occurred while deleting the post.', 'danger')
            return redirect(url_for('posts'))
    else:
        post = ArchivePosts.query.get_or_404(post_id)

    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully.', 'success')
    except Exception as e:
        flash('An error occurred while deleting the post.', 'danger')
    
    return posts()
    
def can_update_or_delete(post_id):
    success = True
    selected_platforms = []
    post = Posts.query.get_or_404(post_id)
    for platform in platforms:
        if getattr(post, f'posted_on_{platform}'):
            platform_model = PLATFORM_MODELS[platform]
            platform_post = platform_model.query.filter_by(original_post_id=post_id).first()
            form = PostForm()
            if platform_post:
                tokens_available = getattr(form, f'{platform}_tokens_available')
                validation_function = getattr(form, f'{platform}_tokens_validation')
                selected_platforms.append(platform)
                if not tokens_available() or not validation_function():
                    success = False
    return success, selected_platforms