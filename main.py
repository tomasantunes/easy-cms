from flask import Flask, render_template, request, flash, jsonify, session, redirect, Markup
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
from werkzeug.utils import secure_filename
import os

def connect_db():
	return sqlite3.connect("easy_cms.db")

db = connect_db()
LOGIN = False
UPLOAD_FOLDER = 'C:\\Users\\tomas\\Documents\\easy-cms\\upload'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = "default_key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
	print(request.method)
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']

		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	return "OK"

@app.route('/upload_avatar', methods=['GET', 'POST'])
def upload_avatar():
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']

		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
			file.save(path)

			user_id = session['user_id']

			if (user_id):
				db = connect_db()
				db.execute('UPDATE users SET avatar = ? WHERE id = ?', [path, user_id])
				db.commit()

	return "OK"

def init():
	sql_users_table = """ CREATE TABLE IF NOT EXISTS users (
							id integer PRIMARY KEY AUTOINCREMENT,
							username text NOT NULL,
							email text NOT NULL,
							password text NOT NULL,
							avatar text
						); """
	db = connect_db()
	c = db.cursor()
	c.execute(sql_users_table)

	sql_posts_table = """ CREATE TABLE IF NOT EXISTS posts (
							id integer PRIMARY KEY AUTOINCREMENT,
							title text,
							content text,
							author integer,
							date date
						); """

	c.execute(sql_posts_table)

	sql_comments_table = """ CREATE TABLE IF NOT EXISTS comments (
							id integer PRIMARY KEY AUTOINCREMENT,
							post_id integer,
							content text,
							author text,
							date date
						); """

	c.execute(sql_comments_table)

	sql_views_table = """ CREATE TABLE IF NOT EXISTS views (
							id integer PRIMARY KEY AUTOINCREMENT,
							page text,
							date date
						); """

	c.execute(sql_views_table)

@app.route("/")
def home():
	db = connect_db()
	c = db.execute('SELECT * FROM posts')
	rows = c.fetchall()
	posts = []

	for row in rows:
		c = db.execute('SELECT * FROM users WHERE id = ?', [row[3]])
		rows = c.fetchall()
		author = rows[0][1]
		post = {
			'id': row[0],
			'title': row[1],
			'content' : Markup(row[2]),
			'author' : author,
			'date' : datetime.datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d'),
			'comments' : [],
		}

		c = db.execute('SELECT * FROM comments INNER JOIN posts on posts.id = comments.post_id;')
		comments = c.fetchall()

		for c in comments:
			comment = {
				'content': c[2],
				'author': c[3]
			}
			post['comments'].append(comment)

		posts.append(post)

	return render_template("home.html", posts=posts)

@app.route('/header')
def header():
    return render_template("header.html")

@app.route("/get-user")
def get_user():
	user_id = session['user_id']
	db = connect_db()
	c = db.execute('SELECT * FROM users WHERE id = ?', [user_id])
	rows = c.fetchall()
	return jsonify(rows)

@app.route("/admin")
def admin():
	if session.get('logged_in') == True and 'user_id' in session and 'username' in session:
		user_id = session['user_id']
		db = connect_db()
		c = db.execute('SELECT * FROM users WHERE id = ?', [user_id])
		rows = c.fetchall()
		print(rows)
		if len(rows) > 0:
			username = session['username']
			data = {'username': username, 'avatar': rows[0][3]}
			return render_template("admin.html", data=data)
		else:
			return redirect("/login")
	else:
		return redirect("/login")

@app.route("/increment-view", methods=['POST'])
def incrementView():
	page = request.form.get('page', "/")
	date = datetime.datetime.now()
	db = connect_db()
	db.execute('INSERT INTO views (page, date) VALUES (?, ?)', [page, date])
	db.commit()
	return "OK"

@app.route("/get-views")
def get_views():
	db = connect_db()
	c = db.execute('SELECT COUNT(*) FROM views')
	rows = c.fetchall()
	return jsonify(rows)

@app.route("/login")
def login():
	return render_template("login.html")

@app.route("/signup")
def register():
	return render_template("signup.html")

def insert_user(username, email, password, avatar):
	db = connect_db()
	db.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', [username, email, generate_password_hash(password)])
	db.commit()

@app.route("/add_user", methods=['POST'])
def add_user():
	username = request.form.get('username', "")
	email = request.form.get('email', "")
	password = request.form.get('password', "")

	if (username != "" and email != "" and password != ""):
		insert_user(username, email, password, "images/default_user.png")
		return redirect("/admin")
	return redirect("/register")
	
@app.route("/add-post", methods=['POST'])
def add_post():
	user_id = session['user_id']
	title = request.form.get('title', "")
	content = request.form.get('content', "")

	date = datetime.datetime.now()

	if (title != "" and content != ""):
		db = connect_db()
		db.execute('INSERT INTO posts (title, content, author, date) VALUES (?, ?, ?, ?)', [title, content, user_id, date])
		db.commit()
		return redirect("/admin")
	return redirect("/admin")

@app.route("/add-comment", methods=['POST'])
def add_comment():
	user_id = session['user_id']
	username = session['username']
	post_id = request.form.get('post-id', "")
	content = request.form.get('content', "")

	date = datetime.datetime.now()

	if (post_id != "" and content != ""):
		db = connect_db()
		db.execute('INSERT INTO comments (post_id, content, author, date) VALUES (?, ?, ?, ?)', [post_id, content, username, date])
		db.commit()
		return redirect("/")
	return redirect("/")

@app.route("/auth", methods=['POST'])
def auth():
	db = connect_db()
	username = request.form.get('username', "")
	password = request.form.get('password', "")

	c = db.execute('SELECT * FROM users WHERE username = ?', [username])
	users = c.fetchall()

	if (len(users) > 0):
		user = users[0]
		if (check_password_hash(user[3], password)):
			session['logged_in'] = True
			session['user_id'] = user[0]
			session['username'] = username
			return jsonify({"error": 0})
	
	return jsonify({"error": 1})

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	session.pop('user_id', None)
	session.pop('username', None)
	return redirect("/admin")
 
if __name__ == "__main__":
	init()
	app.run()