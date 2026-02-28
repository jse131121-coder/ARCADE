import streamlit as st
import json
import os
import uuid
from datetime import datetime

# ================= BASIC =================
st.set_page_config(page_title="RODEWAY", layout="centered")

DATA_FILE = "posts.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def load_posts():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_posts(posts):
    with open(DATA_FILE, "w") as f:
        json.dump(posts, f, indent=4)

# ================= APPLE STYLE =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f4f9ff;
}

.main-title {
    font-size: 40px;
    font-weight: 600;
    letter-spacing: -1px;
    margin-bottom: 0px;
}

.sub {
    color: #7a9cc6;
    font-size: 14px;
    margin-bottom: 40px;
}

.card {
    background: white;
    padding: 28px;
    border-radius: 24px;
    margin-bottom: 25px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
    transition: 0.2s ease-in-out;
}

.card:hover {
    transform: translateY(-3px);
}

.card-title {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 6px;
}

.card-meta {
    font-size: 12px;
    color: #8ca8c9;
    margin-bottom: 14px;
}

textarea, input {
    border-radius: 16px !important;
}

button {
    border-radius: 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION =================
if "write_mode" not in st.session_state:
    st.session_state.write_mode = False

if "selected_post" not in st.session_state:
    st.session_state.selected_post = None

# ================= SIDEBAR =================
st.sidebar.markdown("## RODEWAY")
menu = st.sidebar.radio("", ["피드", "공지"])

if not st.session_state.write_mode:
    if st.sidebar.button("＋ Write"):
        st.session_state.write_mode = True
        st.rerun()

# ================= TITLE =================
st.markdown('<div class="main-title">RODEWAY</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub">{menu}</div>', unsafe_allow_html=True)

posts = load_posts()

# ================= WRITE =================
if st.session_state.write_mode:
    st.markdown("### New Post")

    category = st.selectbox("Category", ["피드", "공지"])
    title = st.text_input("Title")
    content = st.text_area("Content")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Publish"):
            if title and content:
                posts.insert(0, {
                    "id": str(uuid.uuid4()),
                    "category": category,
                    "title": title,
                    "content": content,
                    "date": datetime.now().strftime("%Y.%m.%d %H:%M"),
                    "likes": 0,
                    "comments": []
                })
                save_posts(posts)
                st.session_state.write_mode = False
                st.rerun()

    with col2:
        if st.button("Cancel"):
            st.session_state.write_mode = False
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

# ================= LIST =================
filtered = [p for p in posts if p["category"] == menu]

if not filtered:
    st.info("아직 게시글이 없습니다.")

for post in filtered:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{post['title']}</div>
        <div class="card-meta">{post['date']} · ♥ {post['likes']}</div>
        <div>{post['content'][:120]}...</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1,6])

    with col1:
        if st.button("♥", key="like"+post["id"]):
            post["likes"] += 1
            save_posts(posts)
            st.rerun()

    with col2:
        if st.button("View", key="view"+post["id"]):
            st.session_state.selected_post = post["id"]
            st.rerun()

# ================= DETAIL =================
if st.session_state.selected_post:
    post = next((p for p in posts if p["id"] == st.session_state.selected_post), None)

    if post:
        st.markdown("---")
        st.markdown(f"## {post['title']}")
        st.caption(f"{post['date']} · ♥ {post['likes']}")
        st.write(post["content"])

        st.markdown("### Comments")
        for c in post["comments"]:
            st.write(f"• {c}")

        new_comment = st.text_input("Write a comment")

        if st.button("Add Comment"):
            if new_comment:
                post["comments"].append(new_comment)
                save_posts(posts)
                st.rerun()

        if st.button("Close"):
            st.session_state.selected_post = None
            st.rerun()
