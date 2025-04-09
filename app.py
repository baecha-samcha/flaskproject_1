from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 업로드 폴더가 없으면 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# DB 연결 함수
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.errorhandler(413)
def too_large(e):
    return "🚫 파일이 너무 큽니다! (413)", 413

# 홈 화면
@app.route("/")
def home():
    email = session.get("email")
    return render_template("home.html", email=email)

# 로그인 처리
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
            if user["password"] == password:
                session["email"] = email
                if password == "111111":
                    return redirect(url_for("change_password"))
                return redirect(url_for("home"))
            else:
                return "❌ 비밀번호가 일치하지 않습니다."
        else:
            return "❗ 사용자를 찾을 수 없습니다."
    return render_template("login.html")

# 비밀번호 변경
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        new_pw = request.form["new_password"]
        confirm_pw = request.form["confirm_password"]

        if new_pw != confirm_pw:
            return "❌ 비밀번호가 일치하지 않습니다."

        conn = get_db_connection()
        conn.execute("UPDATE users SET password = ? WHERE email = ?", (new_pw, session["email"]))
        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("change_password.html")

# 로그아웃
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# 게시글 목록
@app.route("/board")
def board():
    if "email" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("board.html", posts=posts)

# 글쓰기 페이지
from flask import abort

@app.route("/write", methods=["GET", "POST"])
def write():
    if "email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # 수동 크기 체크: content-length가 10MB 넘으면 튕기기 (원하면 1GB도 가능)
        content_length = request.content_length
        if content_length is not None and content_length > 5 * 1024 * 1024:
            return render_template("write.html", error="5MB 이상 이미지입니다. 줄여서 올려주세요.")

        
        nickname = request.form["nickname"]
        title = request.form["title"]
        content = request.form["content"]

        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO posts (nickname, title, content) VALUES (?, ?, ?)",
            (nickname, title, content),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("board"))

    return render_template("write.html")

# 게시글 상세 보기 및 댓글 작성
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def view_post(post_id):
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    comments = conn.execute("SELECT * FROM comments WHERE post_id = ?", (post_id,)).fetchall()

    if request.method == "POST":
        if "email" not in session:
            return redirect(url_for("login"))
        nickname = session["email"]
        comment = request.form["comment"]
        conn.execute(
            "INSERT INTO comments (post_id, nickname, comment) VALUES (?, ?, ?)",
            (post_id, nickname, comment),
        )
        conn.commit()

    conn.close()
    return render_template("post.html", post=post, comments=comments)

# 댓글 별도 처리 (사용 안 해도 됨)
@app.route("/add_comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    nickname = request.form['nickname']
    content = request.form['content']

    conn = get_db_connection()
    conn.execute("INSERT INTO comments (post_id, nickname, content) VALUES (?, ?, ?)",
                 (post_id, nickname, content))
    conn.commit()
    conn.close()

    return redirect(url_for('view_post', post_id=post_id))

#실행
if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 5000, app, use_reloader=True, use_debugger=True)
