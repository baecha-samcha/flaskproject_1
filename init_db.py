import sqlite3

conn = sqlite3.connect("users.db")  # 기존 DB에 추가

# 일반콘 세트 테이블
conn.execute("""
CREATE TABLE IF NOT EXISTS dccon_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    thumbnail TEXT
)
""")

# 일반콘 이미지 테이블
conn.execute("""
CREATE TABLE IF NOT EXISTS dccon_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id INTEGER,
    name TEXT,
    filename TEXT,
    FOREIGN KEY (set_id) REFERENCES dccon_sets(id)
)
""")

print("✅ 일반콘 테이블 생성 완료!")


conn.execute("""
CREATE TABLE IF NOT EXISTS user_dccon (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    set_id INTEGER,
    UNIQUE(email, set_id)
)
""")

conn.commit()
conn.close()
print("✅ 다운로드 기록 테이블(user_dccon) 생성 완료!")

