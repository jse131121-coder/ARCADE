import streamlit as st
import sqlite3
import bcrypt
import os
from datetime import datetime

# ================= 기본 설정 =================
st.set_page_config(page_title="RODEWAY", layout="wide")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= 베이비블루 테마 =================
st.markdown("""
<style>
body { background-color: #f0f8ff; }
.stButton>button {
    background-color: #b3e5fc;
    color: black;
    border-radius: 10px;
}
.stTextInput>div>div>input {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ================= DB 연결 =================
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# ================= 테이블 생성 =================
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB,
    nickname TEXT,
    profile_image TEXT,
    role TEXT DEFAULT 'user',
    points INTEGER DEFAULT 0,
    created_at TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    visited_at TEXT
)
""")

conn.commit()

# ================= 관리자 자동 생성 =================
def create_admin():
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        hashed = bcrypt.hashpw("01024773752".encode(), bcrypt.gensalt())
        c.execute("""
        INSERT INTO users (username, password, nickname, role, created_at)
        VALUES (?, ?, ?, 'admin', ?)
        """, ("admin", hashed, "RODEWAY_ADMIN", datetime.now()))
        conn.commit()

create_admin()

# ================= 레벨 계산 =================
def get_level(points):
    return points // 100 + 1

# ================= 세션 초기화 =================
if "user" not in st.session_state:
    st.session_state.user = None

# ================= 방문자 카운트 =================
def record_visit(user_id):
    c.execute("INSERT INTO visits (user_id, visited_at) VALUES (?, ?)",
              (user_id, datetime.now()))
    conn.commit()

def total_visits():
    c.execute("SELECT COUNT(*) FROM visits")
    return c.fetchone()[0]

# ================= 로그인 UI =================
def login():
    st.subheader("로그인")
    username = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user and bcrypt.checkpw(password.encode(), user[2]):
            st.session_state.user = user
            record_visit(user[0])
            st.success("로그인 성공")
            st.rerun()
        else:
            st.error("로그인 실패")

# ================= 회원가입 =================
def register():
    st.subheader("회원가입")
    username = st.text_input("아이디", key="reg_user")
    password = st.text_input("비밀번호", type="password", key="reg_pw")
    nickname = st.text_input("닉네임")

    if st.button("가입하기"):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            c.execute("""
            INSERT INTO users (username, password, nickname, created_at)
            VALUES (?, ?, ?, ?)
            """, (username, hashed, nickname, datetime.now()))
            conn.commit()
            st.success("회원가입 완료")
        except:
            st.error("이미 존재하는 아이디")

# ================= 프로필 =================
def profile():
    user = st.session_state.user
    st.subheader("프로필")

    st.write(f"닉네임: {user[3]}")
    st.write(f"포인트: {user[6]}")
    st.write(f"레벨: {get_level(user[6])}")
    st.write(f"총 방문자 수: {total_visits()}")

    new_nick = st.text_input("닉네임 변경")
    if st.button("닉네임 변경"):
        c.execute("UPDATE users SET nickname=? WHERE id=?",
                  (new_nick, user[0]))
        conn.commit()
        st.success("변경 완료")
        st.rerun()

    uploaded = st.file_uploader("프로필 이미지 업로드")
    if uploaded:
        path = os.path.join(UPLOAD_FOLDER, uploaded.name)
        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())
        c.execute("UPDATE users SET profile_image=? WHERE id=?",
                  (path, user[0]))
        conn.commit()
        st.success("업로드 완료")

# ================= 메인 화면 =================
st.title("🌊 RODEWAY")

if st.session_state.user:
    user = st.session_state.user
    st.sidebar.write(f"👤 {user[3]}")
    st.sidebar.write(f"Level {get_level(user[6])}")
    if st.sidebar.button("프로필"):
        profile()
    if st.sidebar.button("로그아웃"):
        st.session_state.user = None
        st.rerun()
    if user[5] == "admin":
        st.sidebar.success("관리자 모드 활성화")

else:
    menu = st.sidebar.selectbox("메뉴", ["로그인", "회원가입"])
    if menu == "로그인":
        login()
    else:
        register()
