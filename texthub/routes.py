from flask import render_template, url_for, flash, redirect, request
from flask_restx import Api, Resource
from texthub import app, db, bcrypt
from texthub.forms import RegistrationForm, LoginForm, PostForm, UpdateAccountForm, UpdatePlatforms
from texthub.models import User, Posts, ArchivePosts, FacebookPost, TwitterPost
from flask_login import login_user, current_user, logout_user, login_required
import requests, tweepy
from datetime import datetime
from texthub.utils import Twitter, Facebook, platform_names


def update_user_account(form):
    current_user.username = form.username.data
    current_user.email = form.email.data
    db.session.commit()

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
        success = True
        for platform_form in form_platform.platform_forms.values():
            if not platform_form.check_select():
                success = False
        if success:
            flash(f'Platforms have been updated', 'success')
        return redirect(url_for('profile'))
    
    if request.method == 'GET':
        form_name.populate_forms_with_user_data()
        for platform_form in form_platform.platform_forms.values():
            platform_form.populate_forms_with_user_data()
    
    return render_template('profile.html', title='Profile', form_name=form_name, form_platform=form_platform)

@app.route("/editor/<int:post_id>", methods=['GET', 'POST'])
@app.route("/editor", methods=['GET', 'POST'])
@login_required
def editor(post_id=None):

    form = PostForm(platforms=[{'name': platform} for platform in platform_names])

    archived = request.args.get('archived', default=False, type=bool)
    edited = request.args.get('edited', default=False, type=bool)

    if form.validate_on_submit():
        if form.submit.data:
            # Check for Edit Mode, if it wasn't submitted again during the edit mode
            if not edited:
                success = True
                selected_platforms = []
                post_ids = {}
                for platform_form in form.platforms:
                    select_platform = platform_form['name'].data
                    if platform_form.select.data:
                        selected_platforms.append(select_platform)
                        platform_class = globals()[f'{select_platform}']
                        if not platform_class.tokens_available() or not platform_class.tokens_validation():
                            success = False
                if not selected_platforms:
                    flash('Please select at least one platform, or add it to archive and post it later', 'danger')
                    success = False

                if success:
                    posting_status = {platform.lower(): (platform in selected_platforms) for platform in platform_names}
                    
                    post = Posts(
                        title=form.title.data,
                        body=form.body.data,
                        user_id=current_user.id,
                        posted_on=posting_status
                    )
                    message = form.title.data + "\n" + form.body.data
                    for platform in selected_platforms:
                        platform_class = globals()[f'{platform}']
                        post_ids[platform] = platform_class.post(message)

                    db.session.add(post)
                    db.session.commit()

                    for platform in selected_platforms:
                        platform_model = globals()[f'{platform}Post']
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
                        platform_model = globals()[f'{platform}Post']
                        platform_class = globals()[f'{platform}']
                        platform_post = platform_model.query.filter_by(original_post_id=post_id).first()   
                        #uncomment this line when update functions are supporetd
                        #platform_class.update_post(platform_post.platform_post_id, form)
                    post = Posts.query.get_or_404(post_id)
                    post.title = form.title.data
                    post.body = form.body.data
                    post.date_updated = datetime.utcnow()
                    db.session.commit()
                    flash(f'Updated successfully on our app only, not reflected on your platforms, updating feature is not supported now on your selected platforms', 'success')
                    return redirect(url_for('editor'))
        elif form.archive.data:
            # If it wasn't an edited archived post
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
        for select_platform in form.platforms:
            select_platform.select.data = post.posted_on[select_platform['name'].data.lower()]

        return render_template('editor.html', title='Editor', form=form, edit_mode=True, post_id=post_id, archived=archived)
    return render_template('editor.html', title='Editor', form=form, edit_mode=False, archived=archived)

@app.route("/posts", methods=['GET', 'POST'])
@login_required
def posts():

    all_posts = current_user.posts
    archive_posts = current_user.archive_posts
    filtered_posts = {}
    # Filter posts based on the 'posted_on' field for each platform
    filtered_posts = {platform.lower(): [post for post in all_posts if post.posted_on.get(platform.lower())] for platform in platform_names}
    
    return render_template("posts.html", all_posts=all_posts, archive_posts=archive_posts, filtered_posts=filtered_posts, platform_names=platform_names )

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
                platform_model = globals()[f'{platform}Post']
                platform_class = globals()[f'{platform}']
                platform_post = platform_model.query.filter_by(original_post_id=post_id).first()   
                platform_class.delete_post(platform_post.platform_post_id)
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
    for platform, is_posted in post.posted_on.items():
        if  is_posted:
            platform_class = globals()[f'{platform.capitalize()}']
            selected_platforms.append(platform.capitalize())
            if not platform_class.tokens_available() or not platform_class.tokens_validation():
                success = False
    return success, selected_platforms