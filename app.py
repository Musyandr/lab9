# дані для авторизації ("admin", "admin123"), ("user1", "qwerty")

import os
from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3
import secrets
from werkzeug.security import check_password_hash

app = Flask(__name__)
DB_NAME = "points.db"

sessions = {}

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    session_id = request.cookies.get("session_id")
    user = sessions.get(session_id)
    return render_template("index.html", user=user)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session_id = secrets.token_hex(32)
            sessions[session_id] = {"user_id": user["id"], "username": user["username"]}
            resp = make_response(redirect(url_for("index")))
            resp.set_cookie("session_id", session_id, httponly=True)
            return resp
        return render_template("login.html", error="невірний логін або пароль")
    return render_template("login.html")

@app.route("/points")
def all_points():
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return redirect(url_for("login"))
    conn = get_db_connection()
    data = conn.execute("""
        SELECT student.name AS student, course.title AS course, 
               course.semester AS semester, points.value AS value
        FROM points
        JOIN student ON points.id_student = student.id
        JOIN course ON points.id_course = course.id
    """).fetchall()
    conn.close()
    return render_template("points.html", points=data)

@app.route("/students")
def students():
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return redirect(url_for("login"))
    conn = get_db_connection()
    students = conn.execute("SELECT id, name FROM student").fetchall()
    conn.close()
    return render_template("students.html", students=students)

@app.route("/student/<int:student_id>")
def student_points(student_id):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return redirect(url_for("login"))
    conn = get_db_connection()
    student = conn.execute("SELECT name FROM student WHERE id = ?", (student_id,)).fetchone()
    points = conn.execute("""
        SELECT course.title AS course, course.semester AS semester, points.value AS value
        FROM points
        JOIN course ON points.id_course = course.id
        WHERE points.id_student = ?
    """, (student_id,)).fetchall()
    conn.close()
    return render_template("student_points.html", student=student, points=points)

@app.route("/courses")
def courses():
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return redirect(url_for("login"))
    conn = get_db_connection()
    courses = conn.execute("SELECT id, title, semester FROM course").fetchall()
    conn.close()
    return render_template("courses.html", courses=courses)

@app.route("/logout")
def logout():
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("session_id", "", expires=0)
    return resp

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)