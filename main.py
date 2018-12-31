from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

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
 
@app.route("/")
def home():
	return "Hello World!"

@app.route("/admin")
def admin():
	print(str(session))
	if 'username' in session:
		username = session['username']
		return 'Logged in as ' + username + '<br>' + "<b><a href = '/logout'>click here to log out</a></b>"
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

	print(username)
	print(email)
	print(password)

	if (username != "" and email != "" and password != ""):
		db = connect_db()
		db.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', [username, email, generate_password_hash(password)])
		db.commit()
		return redirect("/admin")
	return redirect("/register")
	

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
			session['username'] = username
			print(username)
			print(str(session))
			return redirect("/admin")
	
	return redirect("/admin")

@app.route('/logout')
def logout():
   session.pop('username', None)
   return redirect("/admin")
 
if __name__ == "__main__":
	init()
	app.run()