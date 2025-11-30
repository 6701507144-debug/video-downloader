import streamlit as st
import yt_dlp
import os
import random
import time
import shutil

# --- Configuration ---
st.set_page_config(page_title="CodeX: MVP Downloader", page_icon="⭐", layout="centered")
st.title("⭐ CodeX: MVP Edition (เน้นความเสถียร)")
st.caption("โหมดดึงลิงก์ตรงที่เร็วและง่ายที่สุด")

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --- Functions ---

def get_random_user_agent():
    # ใช้ User Agent ที่หลากหลายเพื่อหลีกเลี่ยงการโดนบล็อก
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
    ]
    return random.choice(user_agents)

# --- Cookie Uploader (Simplified) ---
cookie_path = None
with st.expander("🍪 Cookies (ถ้าโหลดไม่ได้)", expanded=False):
    uploaded_cookie = st.file_uploader("อัปโหลด cookies.txt (สำหรับคลิปส่วนตัว)", type=['txt'], key="cookie_uploader")
    if uploaded_cookie:
        cookie_path = os.path.join(DOWNLOAD_FOLDER, f"temp_cookie_{int(time.time())}.txt")
        # บันทึกไฟล์ลงในโฟลเดอร์ชั่วคราว
        with open(cookie_path, "wb") as f:
            f.write(uploaded_cookie.getbuffer())
        st.success(f"✅ Cookies พร้อมใช้งาน! ({uploaded_cookie.name})")

# --- Main Interface ---
url = st.text_input("🔗 Link URL:", placeholder="วางลิงก์ YouTube/Facebook/TikTok ที่นี่...")

quality_options = {
    "Best Available (MP4/WebM)": 'best',
    "1080p (Full HD)": 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    "720p (HD)": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
    "Audio Only (MP3/M4A)": 'bestaudio/best',
}

selected_quality_name = st.radio("เลือกคุณภาพ:", list(quality_options.keys()))
selected_format = quality_options[selected_quality_name]


if st.button("🔍 ขุดลิงก์ดาวน์โหลด (Generate Link)", type="primary", use_container_width=True):
    if not url:
        st.error("⚠️ กรุณาใส่ลิงก์ก่อนครับ")
        # ลบไฟล์ cookies ชั่วคราวหากมี
        if cookie_path and os.path.exists(cookie_path): os.remove(cookie_path)
        
        st.stop()

    status_placeholder = st.empty()
    status_placeholder.info("🕵️‍♂️ กำลังประมวลผลและขุดหาลิงก์ตรง...")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': get_random_user_agent(),
        'nocheckcertificate': True,
        'format': selected_format,
        # ปิดการดาวน์โหลด/รวมไฟล์ในโหมด Link Generator
        'skip_download': True, 
        'force_generic_extractor': False,
    }
    if cookie_path: ydl_opts['cookiefile'] = cookie_path

    try:
        # 1. Extract Information (download=False)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # yt-dlp จะพยายามเลือก format ที่ดีที่สุดตามที่เรากำหนด
            info_dict = ydl.extract_info(url, download=False)
            
            # 2. หาลิงก์ตรงจากข้อมูลที่ดึงมา
            video_url = None
            
            # ถ้าเลือก Audio Only ให้หา URL ที่เป็น Audio
            if "Audio Only" in selected_quality_name:
                for f in info_dict.get('formats', []):
                    if f.get('acodec') != 'none' and f.get('url'):
                        video_url = f['url']
                        break
            
            # สำหรับ Video (ถ้า yt-dlp เลือก format ที่รวมภาพ/เสียงได้ จะอยู่ที่ 'url')
            if not video_url:
                 # พยายามหาลิงก์ตรงของ format ที่เลือก
                for f in info_dict.get('formats', []):
                    if f.get('format_id') and f.get('url'):
                        # ตรวจสอบว่า format ที่พบตรงกับ format ที่ yt-dlp เลือกหรือไม่
                        # การตรวจสอบนี้ซับซ้อน อาจใช้ info_dict.get('url') แทนเพื่อความง่าย
                        
                        # Fallback: ใช้ลิงก์จาก info_dict โดยตรง (ซึ่งมักจะเป็นลิงก์ของ format ที่ดีที่สุดที่เลือก)
                        if info_dict.get('url'):
                            video_url = info_dict['url']
                            break
                        
                        # Fallback 2: หาลิงก์วิดีโอที่มีภาพและเสียง
                        if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                            video_url = f['url']
                            break
                        
            # ข้อมูลเสริม
            title = info_dict.get('title', 'Unknown Clip')
            thumbnail = info_dict.get('thumbnail', None)

        if video_url:
            status_placeholder.success(f"✅ พบลิงก์ตรงสำหรับ: {title}")
            
            if thumbnail:
                st.image(thumbnail, width=300)
            
            st.markdown(f"""
                <a href="{video_url}" target="_blank" style="text-decoration:none;">
                    <button style="background-color: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer; width: 100%;">
                        ⬇️ คลิกที่นี่เพื่อดาวน์โหลดทันที
                    </button>
                </a>
            """, unsafe_allow_html=True)
            
            st.text_area("ลิงก์ตรง (สำหรับ IDM/โปรแกรมช่วยโหลด):", video_url, height=100)
            
        else:
            status_placeholder.error("❌ ไม่สามารถดึงลิงก์ตรงได้ กรุณาตรวจสอบลิงก์ (อาจเป็นคลิปเฉพาะ หรือต้องการ FFmpeg)")

    except yt_dlp.DownloadError as e:
        status_placeholder.error(f"❌ yt-dlp Error: {e}")
        if "age-restricted" in str(e).lower() or "login" in str(e).lower() or "403" in str(e):
            st.warning("💡 คลิปนี้อาจถูกจำกัดอายุ/ต้องเข้าสู่ระบบ ลองอัปโหลด Cookies ดูครับ")
        elif "Private video" in str(e):
            st.warning("💡 คลิปนี้เป็นส่วนตัว ลองอัปโหลด Cookies ดูครับ")
    except Exception as e:
        status_placeholder.error(f"❌ ข้อผิดพลาดที่ไม่คาดคิด: {e}")
    
    finally:
        # ทำความสะอาด Cookies เสมอ
        if cookie_path and os.path.exists(cookie_path):
            try:
                os.remove(cookie_path)
            except Exception:
                pass