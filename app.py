from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm
app = Flask(__name__)

app.config['SECRET_KEY'] = 'Random charachter'

@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html', title='Home')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}', 'success')
    return render_template('register.html', title='Register', form=form)

@app.route("/login",  methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'test' and form.password.data == '111':
            flash(f'You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash(f'Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

if __name__ == '__main__':
    app.run(debug=True)