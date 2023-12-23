from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from texthub.models import User
from flask_ckeditor import CKEditorField
from flask_login import current_user
from texthub.utils import Twitter, Facebook, platform_names

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

class UpdatePlatformBase(FlaskForm):
    
    def form_valid(self):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def populate_forms_with_user_data(self):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def check_select(self):
        raise NotImplementedError("Subclasses must implement this method.")
 
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