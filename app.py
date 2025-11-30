import streamlit as st
import yt_dlp
import os
import time

st.set_page_config(page_title="Cloud Safe Downloader", page_icon="☁️")
st.title("☁️ Cloud Safe Downloader")
st.caption("โหมดปลอดภัยสำหรับรันบน Server (ไม่มี FFmpeg)")

download_folder = "downloads"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# --- 1. ส่วน Cookies ---
with st.expander("🍪 อัปโหลด Cookies (แก้ปัญหาโหลดไม่ได้)"):
    uploaded_cookie = st.file_uploader("ลากไฟล์ cookies.txt มาวาง", type=['txt'])
    cookie_path = None
    if uploaded_cookie:
        cookie_path = f"temp_cookie_{int(time.time())}.txt"
        with open(cookie_path, "wb") as f:
            f.write(uploaded_cookie.getbuffer())
        st.success("✅ Cookies พร้อมใช้งาน")

# --- 2. รับลิงก์ ---
url = st.text_input("🔗 Link URL:")

# --- 3. ฟังก์ชันโหลด ---
def download_safe():
    if not url: return

    status = st.empty()
    status.info("⏳ กำลังเชื่อมต่อ...")
    
    # การตั้งค่าแบบปลอดภัยที่สุด (ไม่ใช้ FFmpeg, ไม่เร่ง Speed เกินไป)
    ydl_opts = {
        'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        
        # สูตร: เอาไฟล์ MP4 ที่มีอยู่แล้ว (ไม่ต้อง Merge) ไม่เกิน 720p
        'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',
        
        # ปลอมตัวเป็น Android (บางทีหลบ Facebook ได้ดีกว่า Windows)
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
    }

    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            status.info("🚀 กำลังดาวน์โหลด...")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # กันเหนียวเผื่อชื่อไฟล์เพี้ยน
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                for f in os.listdir(download_folder):
                    if base in os.path.join(download_folder, f):
                        filename = os.path.join(download_folder, f)
                        break

        status.success("✅ เสร็จแล้ว!")
        
        # ปุ่มรับไฟล์
        with open(filename, "rb") as f:
            st.download_button("⬇️ รับไฟล์เข้ามือถือ", f, file_name=os.path.basename(filename))
            
    except Exception as e:
        # แสดง Error ชัดๆ ว่าเป็นอะไร
        status.error(f"❌ Error: {e}")
        if "HTTP Error 403" in str(e) or "HTTP Error 404" in str(e):
            st.warning("💡 คำแนะนำ: Facebook บล็อก IP ของ Cloud ครับ -> ลองอัปโหลด cookies.txt จะช่วยได้ 80%")

    # ล้างไฟล์ขยะ
    if cookie_path and os.path.exists(cookie_path):
        os.remove(cookie_path)

if st.button("Start Download"):
    download_safe()