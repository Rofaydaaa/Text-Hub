from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from texthub.models import User
from flask_ckeditor import CKEditorField
from flask_login import current_user
import requests, tweepy

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already register on the system')

class LoginForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already register on the system')
            
    def populate_forms_with_user_data(self):
        self.username.data = current_user.username
        self.email.data = current_user.email

class UpdatePlatforms(FlaskForm):
    select_fb = BooleanField('Facebook')
    token_fb = StringField('Facebook Page Token')
    page_id_fb = StringField('Facebook Page ID')
    select_twitter = BooleanField('Twitter')
    consumer_key_twitter = StringField('Consumer Key')
    consumer_secret_twitter = StringField('Consumer Secret')
    access_token_twitter = StringField('Access Token')
    access_secret_twitter = StringField('Access Secret')
    submit = SubmitField('Update platforms')
        
    def reset_fb_fields(self):
        current_user.token_fb = None
        current_user.page_id_fb = None

    def reset_twitter_fields(self):
        current_user.consumer_key_twitter = None
        current_user.consumer_secret_twitter = None
        current_user.access_token_twitter = None
        current_user.access_secret_twitter = None

    def form_fb_fields_are_valid(self):
        return all([
            self.token_fb.data != "",
            self.page_id_fb.data != "",
        ])

    def form_twitter_fields_are_valid(self):
        return all([
            self.consumer_key_twitter.data != "",
            self.consumer_secret_twitter.data != "",
            self.access_token_twitter.data != "",
            self.access_secret_twitter.data != ""
        ])

    def set_fb_fields(self):
        current_user.token_fb = self.token_fb.data
        current_user.page_id_fb = self.page_id_fb.data

    def set_twitter_fields(self):
        current_user.consumer_key_twitter = self.consumer_key_twitter.data
        current_user.consumer_secret_twitter = self.consumer_secret_twitter.data
        current_user.access_token_twitter = self.access_token_twitter.data
        current_user.access_secret_twitter = self.access_secret_twitter.data

    def populate_forms_with_user_data(self):
        if current_user.token_fb is not None:
            self.select_fb.data = True
            self.token_fb.data = current_user.token_fb
            self.page_id_fb.data = current_user.page_id_fb

        if current_user.consumer_key_twitter is not None:
            self.select_twitter.data = True
            self.consumer_key_twitter.data = current_user.consumer_key_twitter
            self.consumer_secret_twitter.data = current_user.consumer_secret_twitter
            self.access_token_twitter.data = current_user.access_token_twitter
            self.access_secret_twitter.data = current_user.access_secret_twitter

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    body = CKEditorField('Body', validators=[DataRequired("Your text is empty, can't post it!")])
    select_fb = BooleanField('Facebook')
    select_twitter = BooleanField('Twitter')
    submit = SubmitField('Post')
    archive = SubmitField('Add to Archive')

    def fb_tokens_available(self):
        if current_user.token_fb is None or current_user.page_id_fb is None:
            flash("Can't post, please add your Facebook page token.", 'danger')
            return False
        return True
    
    def twitter_tokens_available(self):
        if (current_user.consumer_key_twitter is None or 
            current_user.consumer_secret_twitter is None or
            current_user.access_token_twitter is None or
            current_user.access_secret_twitter is None):
            flash("Can't post, please add your Twitter tokens.", 'danger')
            return False
        return True

    def fb_tokens_validation(self):
        success = True
        access_token = current_user.token_fb
        page_id = current_user.page_id_fb
        debug_token_url = f'https://graph.facebook.com/v18.0/debug_token?input_token={access_token}&access_token={access_token}'

        # Make a GET request to check the token status
        response = requests.get(debug_token_url)
        debug_data = response.json()

        # Check if the token is valid
        if 'error' in debug_data:
            error_type = debug_data['error']['type']
            error_message = debug_data['error']['message']
            success = False

            if 'access token' in error_message.lower() and 'expired' in error_message.lower():
                flash('Your Facebook access token has expired, go to your profile and update it', 'danger')
            elif 'access token could not be decrypted' in error_message.lower():
                flash('Your Facebook access token could not be decrypted, it seems to be a wrong one, go to your profile and update it', 'danger')
            else:
                flash('There is an error in configuring your Facebook token, please follow the instructions on your profile and retry again', 'danger')
        else:
            # Token is valid, proceed with checking the page, permissions

            url = f'https://graph.facebook.com/v18.0/{page_id}/feed'
            data = {'access_token': access_token, 'message': "Test post for token authorization check"}

            r = requests.post(url, data=data)
            page_info = r.json()
            # Check if the page exists
            if 'error' in page_info:
                page_error_type = page_info['error']['type']
                page_error_message = page_info['error']['message']
                success = False

                if page_error_type == 'GraphMethodException' and 'does not exist' in page_error_message:
                    flash('Facebook page with ID {page_id} does not exist or is not accessible, add the right one in your profile and retry again', 'danger')
                elif page_error_type == "OAuthException":
                    flash("You don't have the right permission in your Facebook configurations, "
                            "make sure to set the pages_manage_posts "
                            "and pages_read_engagement as explained in your profile section", 'danger')
                else:
                    flash('There is an error in configuring your Facebook page ID, please follow the instructions on your profile and retry again', 'danger')
            else:
                url = f'https://graph.facebook.com/v18.0/{page_info["id"]}'
                data = {'access_token': access_token}

                r = requests.delete(url, params=data)
        return success

    def twitter_tokens_validation(self):
        try:
            client = tweepy.Client(
                consumer_key=current_user.consumer_key_twitter, consumer_secret=current_user.consumer_secret_twitter,
                access_token=current_user.access_token_twitter, access_token_secret=current_user.access_secret_twitter
            )

            # Attempt to post a test tweet to check for write permissions, as I'm in the free plan and I don'y have access to the update endpoint
            # Not the best method though, but it works :)
            draft_tweet = client.create_tweet(text="Draft tweet for write permiqssion check")

            # Delete the test tweet
            client.delete_tweet(draft_tweet[0]['id'])

            return True      

        except tweepy.errors.Unauthorized as e:
            flash('Your Twitter access tokens are incorrect, go to your profile and update them', 'danger')
        except tweepy.errors.Forbidden as e:
            flash("You don't have permission to perform this action on Twitter, check your account settings as described on your profile", 'danger')
        except tweepy.errors.NotFound as e:
            flash("The requested resource on Twitter was not found, check your account and try again", 'danger')
        except tweepy.errors.TooManyRequests as e:
            flash("You have reached the rate limit for Twitter API requests, please wait and try again later", 'danger')
        except tweepy.errors.TwitterServerError as e:
            flash("Twitter is experiencing server issues, please try again later", 'danger')

        return False

