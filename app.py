from flask import Flask, render_template, request, redirect, session, url_for, abort
from werkzeug.utils import secure_filename
from markupsafe import Markup
import sqlite3
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['BANCON_FOLDER'] = 'static/1bancon'

# 업로드 폴더 없으면 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['BANCON_FOLDER'], exist_ok=True)

# DB 연결 함수
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.errorhandler(413)
def too_large(e):
    return "🚫 파일이 너무 크는듯시다! (413)", 413

@app.route("/")
def home():
    email = session.get("email")
    return render_template("home.html", email=email)

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/board")
def board():
    if "email" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("board.html", posts=posts)

@app.route("/write", methods=["GET", "POST"])
def write():
    if "email" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        content_length = request.content_length
        if content_length is not None and content_length > 5 * 1024 * 1024:
            return render_template("write.html", error="5MB 이상 이미지입력은 제한됩니다.")
        nickname = request.form["nickname"]
        title = request.form["title"]
        content = request.form["content"]
        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
        conn = get_db_connection()
        conn.execute("INSERT INTO posts (nickname, title, content) VALUES (?, ?, ?)", (nickname, title, content))
        conn.commit()
        conn.close()
        return redirect(url_for("board"))
    return render_template("write.html")

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def view_post(post_id):
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    comments = conn.execute("SELECT * FROM comments WHERE post_id = ?", (post_id,)).fetchall()

    if request.method == "POST":
        if "email" not in session:
            return redirect(url_for("login"))
    
        email = session["email"]
        nickname = request.form["nickname"]
        comment = request.form["comment"]
    
        created_at = datetime.now().strftime("%Y.%m.%d %H시 %M분")
    
        conn.execute(
            "INSERT INTO comments (post_id, nickname, content, email, created_at) VALUES (?, ?, ?, ?, ?)",
        (post_id, nickname, comment, email, created_at)
    )
    conn.commit()

    conn.close()
    return render_template("post.html", post=post, comments=comments, email=session.get("email"))


@app.route("/add_comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    nickname = request.form['nickname']
    content = request.form['content']
    conn = get_db_connection()
    conn.execute("INSERT INTO comments (post_id, nickname, content) VALUES (?, ?, ?)", (post_id, nickname, content))
    conn.commit()
    conn.close()
    return redirect(url_for('view_post', post_id=post_id))

@app.route("/create_1bancon", methods=["GET", "POST"])
def create_1bancon():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        names = request.form.getlist("names")
        images = request.files.getlist("images")
        thumbnail = request.files.get("thumbnail")

        thumb_filename = str(uuid.uuid4()) + "_" + secure_filename(thumbnail.filename)
        thumb_path = os.path.join(app.config['BANCON_FOLDER'], thumb_filename)
        thumbnail.save(thumb_path)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO dccon_sets (title, description, thumbnail) VALUES (?, ?, ?)", (title, description, thumb_filename))
        set_id = cur.lastrowid

        for i, image in enumerate(images):
            filename = str(uuid.uuid4()) + "_" + secure_filename(image.filename)
            image_path = os.path.join(app.config['BANCON_FOLDER'], filename)
            image.save(image_path)
            cur.execute("INSERT INTO dccon_items (set_id, name, filename) VALUES (?, ?, ?)", (set_id, names[i], filename))

        conn.commit()
        conn.close()

        return Markup("""
        <script>
            alert(\"🎉 일반콘이 저장되었습니다!\");
            window.location.href = \"/\";
        </script>
        """)
    return render_template("create_1bancon.html")

@app.route("/1bancon_list")
def list_1bancon():
    conn = get_db_connection()
    sets = conn.execute("SELECT * FROM dccon_sets").fetchall()
    conn.close()
    return render_template("1bancon_list.html", sets=sets)

@app.route("/1bancon/<int:set_id>")
def view_1bancon_set(set_id):
    conn = get_db_connection()
    set_info = conn.execute("SELECT * FROM dccon_sets WHERE id = ?", (set_id,)).fetchone()
    items = conn.execute("SELECT * FROM dccon_items WHERE set_id = ?", (set_id,)).fetchall()
    conn.close()

    if set_info is None:
        return "❗ 일반콘 세트를 찾을 수 없습니다.", 404

    return render_template("1bancon_detail.html", set_info=set_info, items=items)

@app.route("/download_1bancon/<int:set_id>")
def download_1bancon(set_id):
    if "email" not in session:
        return redirect(url_for("login"))
    email = session["email"]

    conn = get_db_connection()
    # 이미 다운로드했는지 확인
    existing = conn.execute("SELECT * FROM user_dccon WHERE email = ? AND set_id = ?", (email, set_id)).fetchone()
    if not existing:
        conn.execute("INSERT INTO user_dccon (email, set_id) VALUES (?, ?)", (email, set_id))
        conn.commit()
    conn.close()

    return Markup(f"""
        <script>
        alert('✅ 다운로드 완료! 이제 이 일반콘을 사용할 수 있어요.');
        window.location.href = '/1bancon/{set_id}';
        </script>
    """)

# ✅ 사용자 다운로드한 일반콘 목록 API
from flask import jsonify

@app.route("/api/user_1bancon")
def user_1bancon():
    if "email" not in session:
        return jsonify([])

    email = session["email"]
    conn = get_db_connection()
    sets = conn.execute("""
        SELECT ds.id, ds.title, ds.thumbnail
        FROM dccon_sets ds
        JOIN user_dccon ud ON ds.id = ud.set_id
        WHERE ud.email = ?
    """, (email,)).fetchall()
    conn.close()

    return jsonify([
        {"id": s["id"], "title": s["title"], "thumbnail": s["thumbnail"]} for s in sets
    ])

# ✅ 일반콘 세트 항목 리스트를 반환하는 API
from flask import jsonify

@app.route("/api/1bancon_items/<int:set_id>")
def get_dccon_items(set_id):
    conn = get_db_connection()
    items = conn.execute("SELECT name, filename FROM dccon_items WHERE set_id = ?", (set_id,)).fetchall()
    conn.close()

    return jsonify([
        {"name": item["name"], "filename": item["filename"]} for item in items
    ])

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("0.0.0.0", 5000, app, use_reloader=True, use_debugger=True)
