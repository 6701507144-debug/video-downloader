import streamlit as st
import yt_dlp
import os
import time
import random

# --- 1. การตั้งค่าหน้าเว็บและสไตล์ ---
st.set_page_config(page_title="Hybrid Ultimate Downloader", page_icon="💎", layout="centered")

# CSS ตกแต่งปุ่มให้กดง่ายๆ
st.markdown("""
<style>
    .big-btn {
        display: inline-block;
        width: 100%;
        padding: 15px;
        font-size: 20px;
        font-weight: bold;
        color: white;
        background-color: #FF4B4B;
        text-align: center;
        text-decoration: none;
        border-radius: 10px;
        margin-top: 10px;
    }
    .big-btn:hover {
        background-color: #FF0000;
        color: white;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

st.title("💎 Hybrid Ultimate Downloader")
st.caption("ระบบอัจฉริยะ: ดึงลิงก์ตรง (ไวสุด) + ดาวน์โหลดผ่านเซิร์ฟเวอร์ (สำรอง)")

# --- 2. ระบบจัดการ Cookies (หัวใจสำคัญของ Private Content) ---
cookie_path = None
with st.expander("🍪 Cookies Management (สำหรับคลิปกลุ่มปิด/Facebook/Age-restricted)"):
    st.info("💡 หากโหลดไม่ได้ หรือติด 403 Forbidden ให้อัปโหลดไฟล์ cookies.txt ที่นี่")
    uploaded_cookie = st.file_uploader("ลากไฟล์ cookies.txt มาวางตรงนี้", type=['txt'])
    
    if uploaded_cookie:
        # สร้างชื่อไฟล์สุ่มเพื่อไม่ให้ชนกัน
        cookie_path = f"temp_cookie_{int(time.time())}.txt"
        with open(cookie_path, "wb") as f:
            f.write(uploaded_cookie.getbuffer())
        st.success(f"✅ Cookies พร้อมใช้งาน! (ระบบจะลบเองเมื่อเสร็จงาน)")

# --- 3. ส่วนรับข้อมูล ---
url = st.text_input("🔗 Link URL (YouTube, Facebook, TikTok, etc.):")

# สร้าง Tabs เพื่อแยกโหมดการทำงานให้ชัดเจน
tab1, tab2 = st.tabs(["🚀 โหมดดึงลิงก์ตรง (ไวที่สุด)", "💾 โหมดโหลดผ่าน Server (สำรอง)"])

# --- ฟังก์ชันสุ่ม User Agent (เพื่อความเนียน) ---
def get_user_agent():
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
    ]
    return random.choice(agents)

# ==========================================
# 📍 TAB 1: Link Extractor (ไวที่สุด)
# ==========================================
with tab1:
    st.markdown("<div class='info-box'>โหมดนี้ Server จะไม่โหลดไฟล์ แต่จะไปขุด <b>'ลิงก์จริง'</b> มาให้คุณกด ความเร็วจะเท่ากับเน็ตมือถือของคุณโดยตรง (แนะนำ!)</div>", unsafe_allow_html=True)
    st.write("")
    
    if st.button("🔍 ขุดลิงก์ดาวน์โหลด (Get Link)"):
        if not url:
            st.warning("⚠️ กรุณาใส่ลิงก์ก่อนครับ")
        else:
            status = st.empty()
            status.info("🕵️‍♂️ กำลังเจาะระบบเพื่อหาลิงก์ตรง...")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'user_agent': get_user_agent(),
            }
            if cookie_path: ydl_opts['cookiefile'] = cookie_path

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # extract_info(download=False) คือหัวใจของความไว
                    info = ydl.extract_info(url, download=False)
                    
                    video_url = None
                    title = info.get('title', 'video')
                    thumb = info.get('thumbnail', '')
                    
                    # Logic การหาไฟล์ที่ดีที่สุดที่เล่นได้เลย (มีทั้งภาพและเสียง)
                    formats = info.get('formats', [])
                    # เรียงจากชัดน้อยไปมาก
                    for f in formats:
                        # เงื่อนไข: ต้องเป็น mp4, มี Video codec, มี Audio codec
                        if f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                            video_url = f['url']
                    
                    # ถ้าหา mp4 ไม่เจอ ให้เอา url หลักเลย (เช่น TikTok มักจะเป็นตัวนี้)
                    if not video_url:
                        video_url = info.get('url')

                    if video_url:
                        status.success("✅ เจอเป้าหมาย!")
                        col_img, col_btn = st.columns([1, 2])
                        with col_img:
                            st.image(thumb, use_column_width=True)
                        with col_btn:
                            st.subheader(title)
                            # สร้างปุ่ม HTML สวยๆ
                            st.markdown(f'<a href="{video_url}" target="_blank" class="big-btn">⬇️ คลิกเพื่อดาวน์โหลดทันที</a>', unsafe_allow_html=True)
                            st.caption("*หากกดแล้ววิดีโอเล่น ให้คลิกขวา/กดค้าง แล้วเลือก 'Save Video As'")
                    else:
                        status.error("❌ ไม่พบลิงก์ตรงที่ใช้งานได้ ลองใช้โหมด Server ดูครับ")

            except Exception as e:
                status.error(f"❌ เกิดข้อผิดพลาด: {e}")

# ==========================================
# 📍 TAB 2: Server Download (โหลดผ่าน Cloud)
# ==========================================
with tab2:
    st.write("โหมดนี้ Server จะโหลดไฟล์มาพักไว้ แล้วค่อยส่งให้คุณ (ใช้เวลานานกว่า แต่แก้ปัญหาลิงก์ตรงเสียได้)")
    
    if st.button("💾 ดาวน์โหลดผ่าน Server"):
        if not url:
            st.warning("⚠️ กรุณาใส่ลิงก์ก่อนครับ")
        else:
            download_folder = "downloads"
            if not os.path.exists(download_folder): os.makedirs(download_folder)
            
            status2 = st.empty()
            status2.info("⏳ Server กำลังดาวน์โหลด... (อาจใช้เวลาสักพัก)")
            
            # การตั้งค่าแบบ Safe Mode (ไม่ใช้ FFmpeg เพื่อกัน Error บน Cloud)
            ydl_opts_server = {
                'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                # สูตร Safe: เอา MP4 ที่ดีที่สุดที่มีอยู่แล้ว (ไม่ Merge) ไม่เกิน 720p
                'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',
                'user_agent': get_user_agent(),
            }
            if cookie_path: ydl_opts_server['cookiefile'] = cookie_path

            try:
                with yt_dlp.YoutubeDL(ydl_opts_server) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    # Fix: บางทีชื่อไฟล์เปลี่ยน หรือหาไม่เจอ
                    if not os.path.exists(filename):
                        base = os.path.splitext(filename)[0]
                        for f in os.listdir(download_folder):
                            if base in os.path.join(download_folder, f):
                                filename = os.path.join(download_folder, f)
                                break
                
                status2.success("✅ เรียบร้อย!")
                with open(filename, "rb") as f:
                    st.download_button("⬇️ รับไฟล์เข้าเครื่อง", f, file_name=os.path.basename(filename), mime="video/mp4")
                
                # Cleanup ไฟล์หลังโหลดเสร็จเพื่อประหยัดที่ Cloud
                # os.remove(filename) 

            except Exception as e:
                status2.error(f"❌ Error: {e}")

# --- Cleanup Cookies เมื่อจบการทำงาน ---
if cookie_path and os.path.exists(cookie_path):
    os.remove(cookie_path)