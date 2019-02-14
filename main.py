from flask import Flask, render_template, request, jsonify, session, redirect, Markup
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime

def connect_db():
	return sqlite3.connect("easy_cms.db")

LOGIN = False
db = connect_db()

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = "default_key"

def init():
	sql_users_table = """ CREATE TABLE IF NOT EXISTS users (
							id integer PRIMARY KEY,
							username text NOT NULL,
							email text NOT NULL,
							password text NOT NULL
						); """
	db = connect_db()
	c = db.cursor()
	c.execute(sql_users_table)

	sql_posts_table = """ CREATE TABLE IF NOT EXISTS posts (
							id integer PRIMARY KEY,
							title text,
							content text,
							author integer,
							date date
						); """

	c.execute(sql_posts_table)
 
@app.route("/")
def home():
	db = connect_db()
	c = db.execute('SELECT * FROM posts')
	rows = c.fetchall()
	posts = []
	print(str(posts))
	for row in rows:
		post = {
			'title': row[1],
			'content' : Markup(row[2]),
			'author' : row[3],
			'date' : datetime.datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d')
		}
		posts.append(post)
		
	return render_template("home.html", posts=posts)

@app.route("/admin")
def admin():
	print(str(session))
	if session.get('logged_in') == True and 'username' in session:
		username = session['username']
		data = {'username': username}
		return render_template("admin.html", data=data)
	else:
		return render_template("login.html")

@app.route("/register")
def register():
	return render_template("register.html")

@app.route("/add_user", methods=['POST'])
def add_user():
	username = request.form.get('username', "")
	email = request.form.get('email', "")
	password = request.form.get('password', "")

	if (username != "" and email != "" and password != ""):
		db = connect_db()
		db.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', [username, email, generate_password_hash(password)])
		db.commit()
		return redirect("/admin")
	return redirect("/register")
	
@app.route("/add_post", methods=['POST'])
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
			return redirect("/admin")
	
	return redirect("/admin")

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	session.pop('user_id', None)
	session.pop('username', None)
	return redirect("/admin")
 
if __name__ == "__main__":
	init()
	app.run()