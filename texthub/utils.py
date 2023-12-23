from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_login import current_user
import requests
import tweepy
from texthub import db

platform_names = ['Facebook', 'Twitter']

class SocialMediaBase():

    def set_fields():
        raise NotImplementedError("Subclasses must implement this method.")

    def delete_platform_fields():
        raise NotImplementedError("Subclasses must implement this method.")
    
    def post():
        raise NotImplementedError("Subclasses must implement this method.")
    
    def delete_post():
        raise NotImplementedError("Subclasses must implement this method.")
    
    def update_post():
        raise NotImplementedError("Subclasses must implement this method.")
    
    def tokens_available():
        raise NotImplementedError("Subclasses must implement this method.")

    def tokens_validation():
        raise NotImplementedError("Subclasses must implement this method.")

class Facebook(SocialMediaBase):

    def set_fields(form):
        current_user.token_facebook = form.token_facebook.data
        current_user.page_id_facebook = form.page_id_facebook.data
        db.session.commit()

    def delete_platform_fields():
        current_user.token_faceboook = None
        current_user.page_id_faceboook = None
        db.session.flush()
        print("Before commit:", current_user.token_faceboook, current_user.page_id_faceboook)
        db.session.commit()
        print("After commit:", current_user.token_faceboook, current_user.page_id_faceboook)

    def post(post):
        access_token = current_user.token_facebook
        page_id = current_user.page_id_facebook
        url = f'https://graph.facebook.com/v18.0/{page_id}/feed'
        data = {'access_token': access_token, 'message': post}

        r = requests.post(url, data=data)
        return r.json()['id']
    
    def delete_post(id):
        access_token = current_user.token_facebook

        url = f'https://graph.facebook.com/v18.0/{id}'
        data = {'access_token': access_token}

        requests.delete(url, params=data)
    
    def update_post():
        pass

    def tokens_available():
        if current_user.token_facebook is None or current_user.page_id_facebook is None:
            flash("Can't post, please add your Facebook page token.", 'danger')
            return False
        return True
    
    def tokens_validation():
        success = True
        access_token = current_user.token_facebook
        page_id = current_user.page_id_facebook
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

class Twitter(SocialMediaBase):

    def set_fields(form):
        current_user.consumer_key_twitter = form.consumer_key_twitter.data
        current_user.consumer_secret_twitter = form.consumer_secret_twitter.data
        current_user.access_token_twitter = form.access_token_twitter.data
        current_user.access_secret_twitter = form.access_secret_twitter.data
        db.session.commit()

    def delete_platform_fields():
        current_user.consumer_key_twitter = None
        current_user.consumer_secret_twitter = None
        current_user.access_token_twitter = None
        current_user.access_secret_twitter = None
        db.session.commit()

    def post(tweet):
        client = tweepy.Client(
             consumer_key=current_user.consumer_key_twitter, consumer_secret=current_user.consumer_secret_twitter,
             access_token=current_user.access_token_twitter, access_token_secret=current_user.access_secret_twitter
         )

        response = client.create_tweet(text=tweet)
        return response.data['id']

    def delete_post():
        client = tweepy.Client(
             consumer_key=current_user.consumer_key_twitter, consumer_secret=current_user.consumer_secret_twitter,
             access_token=current_user.access_token_twitter, access_token_secret=current_user.access_secret_twitter
         )

        client.delete_tweet(id)

    def update_post():
        pass

    def tokens_available():
        if (current_user.consumer_key_twitter is None or 
            current_user.consumer_secret_twitter is None or
            current_user.access_token_twitter is None or
            current_user.access_secret_twitter is None):
            flash("Can't post, please add your Twitter tokens.", 'danger')
            return False
        return True

    def tokens_validation():
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