from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 아무 문자열이나 써도 됨

# DB 연결 함수
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# 홈 화면 - 로그인 여부에 따라 다르게 표시
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

# 비밀번호 변경 페이지
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

# 실행
if __name__ == "__main__":
    app.run(debug=True)
