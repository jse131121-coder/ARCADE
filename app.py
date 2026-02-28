import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime

# ================= 기본 설정 =================
st.set_page_config(page_title="RODEWAY", layout="wide")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= 테마 =================
if "dark" not in st.session_state:
    st.session_state.dark = False

if st.sidebar.button("🌙 다크모드"):
    st.session_state.dark = not st.session_state.dark

if st.session_state.dark:
    st.markdown("""
    <style>
    body { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    body { background-color: #f0f8ff; }
    .stButton>button {background-color:#b3e5fc;border-radius:10px;}
    </style>
    """, unsafe_allow_html=True)

# ================= DB =================
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# ================= 테이블 =================
c.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
nickname TEXT,
profile_image TEXT,
role TEXT DEFAULT 'user',
points INTEGER DEFAULT 0,
is_banned INTEGER DEFAULT 0,
created_at TEXT)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS posts(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
content TEXT,
author_id INTEGER,
category TEXT,
image TEXT,
file TEXT,
created_at TEXT,
views INTEGER DEFAULT 0,
likes INTEGER DEFAULT 0,
dislikes INTEGER DEFAULT 0,
is_notice INTEGER DEFAULT 0,
is_secret INTEGER DEFAULT 0)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS comments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
post_id INTEGER,
author_id INTEGER,
content TEXT,
parent_id INTEGER,
likes INTEGER DEFAULT 0,
created_at TEXT)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reports(
id INTEGER PRIMARY KEY AUTOINCREMENT,
target_type TEXT,
target_id INTEGER,
reporter_id INTEGER,
reason TEXT,
created_at TEXT)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS notifications(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
message TEXT,
is_read INTEGER DEFAULT 0,
created_at TEXT)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS visits(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
visited_at TEXT)
""")

conn.commit()

# ================= 해시 =================
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def check_pw(p, h):
    return hash_pw(p) == h

# ================= 관리자 자동 생성 =================
c.execute("SELECT * FROM users WHERE role='admin'")
if not c.fetchone():
    c.execute("""
    INSERT INTO users(username,password,nickname,role,created_at)
    VALUES(?,?,?,?,?)
    """, ("admin", hash_pw("01024773752"), "RODEWAY_ADMIN","admin",datetime.now()))
    conn.commit()

# ================= 세션 =================
if "user" not in st.session_state:
    st.session_state.user = None

# ================= 유틸 =================
def add_points(uid, amt):
    c.execute("UPDATE users SET points=points+? WHERE id=?", (amt, uid))
    conn.commit()

def level(p):
    return p//100 + 1

def rank(p):
    if p < 100: return "Newbie"
    if p < 300: return "Member"
    if p < 700: return "Core"
    return "Legend"

# ================= 로그인 =================
def login():
    st.subheader("로그인")
    u = st.text_input("아이디")
    p = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        c.execute("SELECT * FROM users WHERE username=?", (u,))
        user = c.fetchone()
        if user and check_pw(p, user[2]):
            if user[7]==1:
                st.error("정지된 계정")
                return
            st.session_state.user = user
            c.execute("INSERT INTO visits(user_id,visited_at) VALUES(?,?)",(user[0],datetime.now()))
            conn.commit()
            st.rerun()
        else:
            st.error("실패")

# ================= 회원가입 =================
def register():
    st.subheader("회원가입")
    u = st.text_input("아이디")
    p = st.text_input("비밀번호", type="password")
    n = st.text_input("닉네임")
    if st.button("가입"):
        try:
            c.execute("""
            INSERT INTO users(username,password,nickname,created_at)
            VALUES(?,?,?,?)
            """,(u,hash_pw(p),n,datetime.now()))
            conn.commit()
            st.success("완료")
        except:
            st.error("이미 존재")

# ================= 글쓰기 =================
def write_post():
    st.subheader("글쓰기")
    t = st.text_input("제목")
    ctt = st.text_area("내용")
    cat = st.selectbox("카테고리",["피드","공지"])
    img = st.file_uploader("이미지")
    fil = st.file_uploader("파일")
    secret = st.checkbox("비밀글")
    notice = 0
    if st.session_state.user[5]=="admin":
        notice = st.checkbox("공지등록")
    if st.button("작성"):
        img_path=None; file_path=None
        if img:
            img_path=os.path.join(UPLOAD_FOLDER,img.name)
            with open(img_path,"wb") as f: f.write(img.getbuffer())
        if fil:
            file_path=os.path.join(UPLOAD_FOLDER,fil.name)
            with open(file_path,"wb") as f: f.write(fil.getbuffer())
        c.execute("""
        INSERT INTO posts(title,content,author_id,category,image,file,created_at,is_notice,is_secret)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,(t,ctt,st.session_state.user[0],cat,img_path,file_path,datetime.now(),notice,secret))
        conn.commit()
        add_points(st.session_state.user[0],10)
        st.rerun()

# ================= 게시판 =================
def list_posts():
    st.subheader("게시판")
    search=st.text_input("검색")
    sort=st.selectbox("정렬",["최신순","인기순","조회순"])
    query="SELECT * FROM posts WHERE 1=1"
    if search:
        query+=f" AND (title LIKE '%{search}%' OR content LIKE '%{search}%')"
    if sort=="최신순":
        query+=" ORDER BY is_notice DESC,id DESC"
    elif sort=="인기순":
        query+=" ORDER BY is_notice DESC,likes DESC"
    else:
        query+=" ORDER BY is_notice DESC,views DESC"
    c.execute(query)
    posts=c.fetchall()
    per=5
    pages=max(1,len(posts)//per+1)
    page=st.number_input("페이지",1,pages,1)
    for p in posts[(page-1)*per:page*per]:
        if p[11]==1: st.markdown("📌 공지")
        st.markdown(f"### {p[1]}")
        st.write(f"조회 {p[8]} 👍{p[9]}")
        if st.button("보기",key=p[0]):
            view_post(p[0])

# ================= 상세 =================
def view_post(pid):
    c.execute("UPDATE posts SET views=views+1 WHERE id=?",(pid,))
    conn.commit()
    c.execute("SELECT * FROM posts WHERE id=?",(pid,))
    p=c.fetchone()
    if p[12]==1 and st.session_state.user[0]!=p[3] and st.session_state.user[5]!="admin":
        st.warning("비밀글")
        return
    st.subheader(p[1])
    st.write(p[2])
    if p[5]: st.image(p[5])
    if p[6]:
        with open(p[6],"rb") as f:
            st.download_button("파일다운",f,file_name=p[6])
    if st.button("👍"):
        c.execute("UPDATE posts SET likes=likes+1 WHERE id=?",(pid,))
        add_points(p[3],2)
        conn.commit(); st.rerun()

    # 댓글
    st.subheader("댓글")
    cm=st.text_input("댓글")
    if st.button("작성"):
        c.execute("""
        INSERT INTO comments(post_id,author_id,content,created_at)
        VALUES(?,?,?,?)
        """,(pid,st.session_state.user[0],cm,datetime.now()))
        conn.commit()
        add_points(st.session_state.user[0],3)
        st.rerun()
    c.execute("SELECT * FROM comments WHERE post_id=?",(pid,))
    for com in c.fetchall():
        st.write(f"- {com[3]} 👍{com[5]}")

# ================= 관리자 =================
def admin_panel():
    st.subheader("관리자 패널")
    c.execute("SELECT * FROM reports")
    for r in c.fetchall():
        st.write(r)

# ================= 메인 =================
st.title("🌊 RODEWAY")

if st.session_state.user:
    u=st.session_state.user
    st.sidebar.write(f"{u[3]} | Lv{level(u[6])} | {rank(u[6])}")
    if st.sidebar.button("게시판"): list_posts()
    if st.sidebar.button("글쓰기"): write_post()
    if u[5]=="admin":
        if st.sidebar.button("관리자"): admin_panel()
    if st.sidebar.button("로그아웃"):
        st.session_state.user=None
        st.rerun()
else:
    m=st.sidebar.selectbox("메뉴",["로그인","회원가입"])
    if m=="로그인": login()
    else: register()
