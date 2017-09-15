# Import statements
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
	render_template, flash

# Application Instance
app = Flask(__name__) # Create the instance
app.config.from_object(__name__) # Load config from this file

# Define root directory
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

# Load default config and override config from an environment variable
app.config.update(dict(
	DATABASE=os.path.join(PROJECT_ROOT, 'tmp/FlaskApp.db'),
	SECRET_KEY='development key',
	USERNAME='admin',
	PASSWORD='password',
	DEBUG=True
))
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)

#------------------ Helper Functions
# Create a method that allows easy connections to the SQLite Database
def connect_db():
	"""Connects to the specific database."""
	rv = sqlite3.connect(app.config['DATABASE'], timeout=5)
	# rv = sqlite3.connect('FlaskApp.db', timeout=5)
	rv.row_factory = sqlite3.Row
	return rv

# Open a new database connection if none have been created
def get_db():
	"""Opens a new database connection if there is none yet for the current	application context."""
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

# Handle closing and disconnecting
@app.teardown_appcontext
# An app is 'teared down' whenever a request is finished
# Either everything went well, or an exception was thrown
def close_db(error):
	"""Closes the database again at the end of the request."""
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

# Add some methods to initialize the application's database
def init_db():
	db = get_db()
	with app.open_resource('schema.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()

@app.cli.command('initdb')
# Binds the following method to the CLI command 'initdb'
def initdb_command():
	"""Initializes the database."""
	init_db()
	print('Initialized the database.')

#------------------ Views
# Routing to views are handled using the route method on the flask app

# View for home page. Display all database entries
@app.route('/')
def show_entries():
	db = get_db()
	cur = db.execute('select title, text from entries order by id desc')
	entries = cur.fetchall()
	return render_template('show_entries.html', entries=entries)

# View for adding a new template.
@app.route('/add', methods=['POST'])
def add_entry():
	if not session.get('logged_in'):
		#abort(401)
	db = get_db()
	db.execute('insert into entries (title, text) values (?, ?)',
			[request.form['title'], request.form['text']])
	db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))

# Login handling. Check against the config file (Only one user available on this app)
@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['username'] != app.config['USERNAME']:
			error = 'Invalid username'
		elif request.form['password'] != app.config['PASSWORD']:
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

# Handle the logout, clear the session variable
@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))
