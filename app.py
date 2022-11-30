import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging

DB_CONNECTION_COUNT = 0
def db_connection_release():
    global DB_CONNECTION_COUNT
    DB_CONNECTION_COUNT = DB_CONNECTION_COUNT - 1

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global DB_CONNECTION_COUNT
    DB_CONNECTION_COUNT = DB_CONNECTION_COUNT  + 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    db_connection_release()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    db_connection_release()
    return render_template('index.html', posts=posts)

@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    ## log line
    app.logger.info('Status request successfull')
    return response


@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    posts_cnt = 0
    if posts:
        posts_cnt = len(posts)
    global DB_CONNECTION_COUNT
    response = app.response_class(
            response=json.dumps({"status":"success","code":0,"data":{"db_connection_count":DB_CONNECTION_COUNT,"post_count":posts_cnt}}),
            status=200,
            mimetype='application/json'
    )
    connection.close()
    db_connection_release()
    return response


# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info(f'Not found article id {post_id}')
        return render_template('404.html'), 404
    else:
        app.logger.info(f'Article "{post[2]}" is retrieved')
        return render_template('post.html', post=post)
## log line
    app.logger.info('Status request successfull')  

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info(f'Page "about us" is retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            db_connection_release()
            app.logger.info(f'New article {title} is created')

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
