from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

def connect_db():
	return sqlite3.connect("easy_cms.db")

LOGIN = False
db = connect_db()

app = Flask(__name__)
app.config.from_object(__name__)

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
	if (app.config["LOGIN"] == True):
		return "admin page"
	else:
		return render_template("login.html")

@app.route("/register")
def register():
	return render_template("register.html")

@app.route("/add_user", methods=['POST'])
def add_user():
	username = request.args.get('username', "")
	email = request.args.get('email', "")
	password = request.args.get('password', "")

	db = connect_db()
	db.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', [username, email, generate_password_hash(password)])
	db.commit()

	return jsonify({"status": "OK"})

@app.route("/auth", methods=['POST'])
def auth():
	db = connect_db()
	username = request.args.get('username', "")
	password = request.args.get('password', "")

	c = db.execute('SELECT * FROM users WHERE username = ?', [username])
	users = c.fetchall()

	if (len(users) > 0):
		user = users[0]
		if (check_password_hash(user[3], password)):
			app.config["LOGIN"] = True
			return jsonify({"status": "OK"})
	
	return jsonify({"status": "ERROR"})
 
if __name__ == "__main__":
	init()
	app.run()