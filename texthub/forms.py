from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from texthub.models import User
from flask_ckeditor import CKEditorField
from flask_login import current_user
from texthub.utils import Twitter, Facebook, Medium, Dev, platform_names

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
    submit = SubmitField('Update platforms')
    
    def __init__(self, *args, **kwargs):
        super(UpdatePlatforms, self).__init__(*args, **kwargs)
        
        # Create a dictionary to store instances of platform forms
        self.platform_forms = {}
        for platform_name in platform_names:
            form_class = globals()[f'Update{platform_name}']
            self.platform_forms[platform_name.lower()] = form_class(prefix=platform_name.lower())

class PlatformForm(FlaskForm):
    name = StringField('Name')
    select = BooleanField('Select', default=False)

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    body = CKEditorField('Body', validators=[DataRequired("Your text is empty, can't post it!")])
    submit = SubmitField('Post')
    archive = SubmitField('Add to Archive')

    platforms = FieldList(FormField(PlatformForm), min_entries=1)

class UpdatePlatformBase(FlaskForm):
    
    def form_valid(self):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def populate_forms_with_user_data(self):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def check_select(self):
        raise NotImplementedError("Subclasses must implement this method.")

class UpdateFacebook(UpdatePlatformBase):
    select = BooleanField('Facebook')
    token_facebook = StringField('Facebook Page Token')
    page_id_facebook = StringField('Facebook Page ID')

    def form_valid(self):
        return all([
            self.token_facebook.data != "",
            self.page_id_facebook.data != "",
        ])
    
    def populate_forms_with_user_data(self):
        if current_user.token_facebook is not None:
            self.select.data = True
            self.token_facebook.data = current_user.token_facebook
            self.page_id_facebook.data = current_user.page_id_facebook
    
    def check_select(self):
        if not self.select.data:
            Facebook.delete_platform_fields()
        elif self.form_valid():
            Facebook.set_fields(self)
        else:
            Facebook.delete_platform_fields()
            flash('Adding platform failed, configure your Facebook page data', 'danger')
            return False
        return True
        
class UpdateTwitter(UpdatePlatformBase):
    select = BooleanField('Twitter')
    consumer_key_twitter = StringField('Consumer Key')
    consumer_secret_twitter = StringField('Consumer Secret')
    access_token_twitter = StringField('Access Token')
    access_secret_twitter = StringField('Access Secret')
    
    def form_valid(self):
        return all([
            self.consumer_key_twitter.data != "",
            self.consumer_secret_twitter.data != "",
            self.access_token_twitter.data != "",
            self.access_secret_twitter.data != ""
        ])

    def populate_forms_with_user_data(self):
        if current_user.consumer_key_twitter is not None:
            self.select.data = True
            self.consumer_key_twitter.data = current_user.consumer_key_twitter
            self.consumer_secret_twitter.data = current_user.consumer_secret_twitter
            self.access_token_twitter.data = current_user.access_token_twitter
            self.access_secret_twitter.data = current_user.access_secret_twitter
    
    def check_select(self):
        if not self.select.data:
            Twitter.delete_platform_fields()
        elif self.form_valid():
            Twitter.set_fields(self)
        else:
            Twitter.delete_platform_fields()
            flash('Adding platform failed, configure your Twitter page data', 'danger')
            return False
        return True
    
class UpdateMedium(UpdatePlatformBase):
    select = BooleanField('Medium')
    integration_token_medium = StringField('Integration token')
    
    def form_valid(self):
        return all([
            self.integration_token_medium.data != "",
        ])

    def populate_forms_with_user_data(self):
        if current_user.integration_token_medium is not None:
            self.select.data = True
            self.integration_token_medium.data = current_user.integration_token_medium
    
    def check_select(self):
        if not self.select.data:
            Medium.delete_platform_fields()
        elif self.form_valid():
            Medium.set_fields(self)
        else:
            Medium.delete_platform_fields()
            flash('Adding platform failed, configure your Medium token', 'danger')
            return False
        return True
    
class UpdateDev(UpdatePlatformBase):
    select = BooleanField('DEV.to')
    integration_token_dev = StringField('Integration token')
    
    def form_valid(self):
        return all([
            self.integration_token_dev.data != "",
        ])

    def populate_forms_with_user_data(self):
        if current_user.integration_token_dev is not None:
            self.select.data = True
            self.integration_token_dev.data = current_user.integration_token_dev
    
    def check_select(self):
        if not self.select.data:
            Dev.delete_platform_fields()
        elif self.form_valid():
            Dev.set_fields(self)
        else:
            Dev.delete_platform_fields()
            flash('Adding platform failed, configure your Dev.to token', 'danger')
            return False
        return True
    