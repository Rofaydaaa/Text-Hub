from texthub import app, db

@app.before_request
def init_db():
    with app.app_context():
        db.create_all()
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)