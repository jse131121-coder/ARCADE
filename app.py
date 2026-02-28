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


# ================= STYLE =================
st.markdown("""
<style>
body {
    background-color: #eaf6ff;
}
.post-card {
    background: white;
    padding: 20px;
    border-radius: 20px;
    margin-bottom: 15px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}
.title {
    font-size: 18px;
    font-weight: 600;
}
.meta {
    font-size: 12px;
    color: gray;
}
</style>
""", unsafe_allow_html=True)


# ================= SESSION =================
if "write_mode" not in st.session_state:
    st.session_state.write_mode = False

if "selected_post" not in st.session_state:
    st.session_state.selected_post = None


# ================= SIDEBAR =================
st.sidebar.title("RODEWAY")
menu = st.sidebar.radio("Menu", ["피드", "공지"])

if not st.session_state.write_mode:
    if st.sidebar.button("✏️ Write"):
        st.session_state.write_mode = True
        st.rerun()


# ================= TITLE =================
st.title("RODEWAY")
st.caption(menu)


posts = load_posts()

# ================= WRITE =================
if st.session_state.write_mode:
    st.markdown("### New Post")

    category = st.selectbox("Category", ["피드", "공지"])
    title = st.text_input("Title")
    content = st.text_area("Content")

    if st.button("Submit"):
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

    if st.button("Cancel"):
        st.session_state.write_mode = False
        st.rerun()

    st.markdown("---")


# ================= LIST =================
filtered = [p for p in posts if p["category"] == menu]

if menu == "공지":
    filtered = sorted(filtered, key=lambda x: x["date"], reverse=True)

if not filtered:
    st.info("게시글이 없습니다.")

for post in filtered:
    with st.container():
        st.markdown(f"""
        <div class="post-card">
            <div class="title">{post['title']}</div>
            <div class="meta">{post['date']} · ❤️ {post['likes']}</div>
            <hr>
            <div>{post['content'][:100]}...</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1,1,3])

        with col1:
            if st.button("❤️", key="like"+post["id"]):
                post["likes"] += 1
                save_posts(posts)
                st.rerun()

        with col2:
            if st.button("보기", key="view"+post["id"]):
                st.session_state.selected_post = post["id"]
                st.rerun()


# ================= DETAIL =================
if st.session_state.selected_post:
    post = next((p for p in posts if p["id"] == st.session_state.selected_post), None)

    if post:
        st.markdown("## 상세 보기")
        st.markdown(f"### {post['title']}")
        st.caption(f"{post['date']} · ❤️ {post['likes']}")
        st.write(post["content"])

        st.markdown("### 댓글")

        for c in post["comments"]:
            st.write(f"- {c}")

        new_comment = st.text_input("댓글 입력", key="comment_input")

        if st.button("댓글 등록"):
            if new_comment:
                post["comments"].append(new_comment)
                save_posts(posts)
                st.rerun()

        if st.button("닫기"):
            st.session_state.selected_post = None
            st.rerun()
