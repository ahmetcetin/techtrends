import sqlite3
import subprocess
import sys
from logging.config import dictConfig

from flask import (Flask, flash, json, jsonify, redirect, render_template,
                   request, url_for)
from werkzeug.exceptions import abort


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to count the number of posts
def count_posts():
    connection = get_db_connection()

    command = 'lsof database.db'
    lsof = subprocess.check_output(command, shell=True, stderr = subprocess.STDOUT)

    count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()
    connection.close()

    # Return number of connections (reduce 1 for header of lsof) & numberof posts
    return len(lsof.splitlines()) - 1, count[0]

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {'default': {
        'format': '%(levelname)s:%(module)s:%(asctime)s, %(message)s',
    }},
    'handlers': {
       "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console']
    }
})

# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define the health check route
@app.route('/healthz')
def healthz():
    return 'result: OK - healthy', 200

@app.route('/metrics')
def metric():
    number_of_connection, number_of_posts = count_posts()
    return jsonify(db_connection_count=number_of_connection, post_count=number_of_posts), 200

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)

    if post is None:
        app.logger.error('Article id "%s" not found!', post_id)
        return render_template('404.html'), 404
    else:
        app.logger.info('Article "%s" retrieved!', post['title'])
        return render_template('post.html', post=post), 200

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('"About us" page accessed')
    return render_template('about.html')

# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
            app.logger.error('New post without title')
            return render_template('create.html')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                        (title, content))
            connection.commit()
            connection.close()

            app.logger.info('New post created with title "%s"', title)

            return redirect(url_for('index'))
    else:
        app.logger.info('"Create post" page accessed')
        return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='3111')
