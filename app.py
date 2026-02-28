import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime

# ================= 기본 설정 =================
st.set_page_config(page_title="RODEWAY", layout="wide")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= 🎨 DESIGN PACK =================
st.markdown("""
<style>

/* 배경 */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #eaf6ff 0%, #f6fbff 100%);
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 헤더 숨김 */
header {visibility: hidden;}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #ffffffcc;
    backdrop-filter: blur(15px);
    border-right: 1px solid #e3f2fd;
}

/* 카드 */
.card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    margin-bottom: 20px;
    transition: 0.25s ease;
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(0,0,0,0.09);
}

/* 버튼 */
.stButton>button {
    background: #90CAF9;
    color: #0d1b2a;
    border-radius: 30px;
    padding: 10px 22px;
    border: none;
    font-weight: 600;
    transition: 0.25s;
}
.stButton>button:hover {
    background: #64B5F6;
    transform: scale(1.05);
}

/* 입력창 */
.stTextInput>div>div>input,
.stTextArea textarea {
    border-radius: 14px;
    border: 1px solid #dceeff;
    padding: 10px;
}

/* 댓글 */
.comment-box {
    background: #f3f9ff;
    padding: 12px;
    border-radius: 14px;
    margin-bottom: 8px;
    font-size: 14px;
}

/* 공지 배지 */
.notice-badge {
    background: #64B5F6;
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    display: inline-block;
    margin-bottom: 6px;
}

h1,h2,h3 {font-weight:700;}

</style>
""", unsafe_allow_html=True)

# ================= DB =================
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
nickname TEXT,
role TEXT DEFAULT 'user',
points INTEGER DEFAULT 0,
created_at TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS posts(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
author_id INTEGER,
category TEXT,
created_at TEXT,
views INTEGER DEFAULT 0,
likes INTEGER DEFAULT 0,
is_notice INTEGER DEFAULT 0)""")

c.execute("""CREATE TABLE IF NOT EXISTS comments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
post_id INTEGER,
author_id INTEGER,
content TEXT,
created_at TEXT,
likes INTEGER DEFAULT 0)""")

conn.commit()

# ================= 해시 =================
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def check_pw(p,h): return hash_pw(p)==h

# 관리자 자동 생성
c.execute("SELECT * FROM users WHERE role='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users(username,password,nickname,role,created_at) VALUES(?,?,?,?,?)",
              ("admin",hash_pw("01024773752"),"RODEWAY_ADMIN","admin",datetime.now()))
    conn.commit()

if "user" not in st.session_state:
    st.session_state.user=None

# ================= 로그인 =================
def login():
    st.subheader("Login")
    u=st.text_input("ID")
    p=st.text_input("Password",type="password")
    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE username=?",(u,))
        user=c.fetchone()
        if user and check_pw(p,user[2]):
            st.session_state.user=user
            st.rerun()
        else:
            st.error("Invalid")

def register():
    st.subheader("Register")
    u=st.text_input("ID")
    p=st.text_input("Password",type="password")
    n=st.text_input("Nickname")
    if st.button("Create"):
        try:
            c.execute("INSERT INTO users(username,password,nickname,created_at) VALUES(?,?,?,?)",
                      (u,hash_pw(p),n,datetime.now()))
            conn.commit()
            st.success("Done")
        except:
            st.error("Already exists")

# ================= WRITE BUTTON =================
if "write_mode" not in st.session_state:
    st.session_state.write_mode = False

if st.button("✏️ Write"):
    st.session_state.write_mode = True


# ================= WRITE FORM =================
if st.session_state.write_mode:
    st.markdown("### New Post")

    title = st.text_input("Title")
    content = st.text_area("Content")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Submit"):
            if title and content:
                posts = load_posts()

                posts.insert(0, {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "content": content,
                    "date": datetime.now().strftime("%Y.%m.%d %H:%M")
                })

                save_posts(posts)

                st.session_state.write_mode = False
                st.success("Posted successfully!")
                st.rerun()

    with col2:
        if st.button("Cancel"):
            st.session_state.write_mode = False
            st.rerun()
# ================= 게시판 =================
def list_posts():
    st.subheader("Feed")
    c.execute("SELECT * FROM posts ORDER BY is_notice DESC, id DESC")
    posts=c.fetchall()
    for p in posts:
        st.markdown(f"""
        <div class="card">
            {"<div class='notice-badge'>NOTICE</div>" if p[8]==1 else ""}
            <h3>{p[1]}</h3>
            <p style='color:gray;font-size:13px;'>조회 {p[6]} · 👍 {p[7]}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open",key=p[0]):
            view_post(p[0])

def view_post(pid):
    c.execute("UPDATE posts SET views=views+1 WHERE id=?",(pid,))
    conn.commit()
    c.execute("SELECT * FROM posts WHERE id=?",(pid,))
    p=c.fetchone()
    st.markdown(f"<div class='card'><h2>{p[1]}</h2><p>{p[2]}</p></div>",unsafe_allow_html=True)

    if st.button("👍"):
        c.execute("UPDATE posts SET likes=likes+1 WHERE id=?",(pid,))
        conn.commit()
        st.rerun()

    st.subheader("Comments")
    cm=st.text_input("Write comment")
    if st.button("Send"):
        c.execute("INSERT INTO comments(post_id,author_id,content,created_at) VALUES(?,?,?,?)",
                  (pid,st.session_state.user[0],cm,datetime.now()))
        conn.commit()
        st.rerun()

    c.execute("SELECT * FROM comments WHERE post_id=?",(pid,))
    for com in c.fetchall():
        st.markdown(f"""
        <div class="comment-box">
        {com[3]} 👍 {com[5]}
        </div>
        """, unsafe_allow_html=True)

# ================= MAIN =================
st.title("🌊 RODEWAY")

if st.session_state.user:
    st.sidebar.write(st.session_state.user[3])
    if st.sidebar.button("Feed"): list_posts()
    if st.sidebar.button("Write"): write_post()
    if st.sidebar.button("Logout"):
        st.session_state.user=None
        st.rerun()
else:
    m=st.sidebar.selectbox("Menu",["Login","Register"])
    if m=="Login": login()
    else: register()
