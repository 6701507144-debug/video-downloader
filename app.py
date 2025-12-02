import streamlit as st
import yt_dlp
import os
import random
import time
import shutil
import re

# --- 1. Global Configurations & Utility Functions ---

# โฟลเดอร์เก็บไฟล์ชั่วคราว
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ตรวจสอบ FFmpeg (ความเสถียร)
FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg.exe"
IS_FFMPEG_READY = os.path.exists(FFMPEG_PATH) or (shutil.which("ffmpeg") is not None)

def get_random_user_agent():
    """Returns a random User-Agent string to avoid detection."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    ]
    return random.choice(user_agents)

# Initialize Session State
if 'cookie_path' not in st.session_state: st.session_state.cookie_path = None
if 'downloaded_file_path' not in st.session_state: st.session_state.downloaded_file_path = None


# --- 2. Streamlit UI/UX and CSS Styling ---

st.set_page_config(page_title="CodeX: Ghost Downloader", page_icon="👻", layout="wide")

st.markdown("""
<style>
    /* Ghost Dark Theme */
    body { color: #c9d1d9; background-color: #010409; }
    .stApp { background-color: #010409; }
    
    /* Headers (Ghost Glow) */
    h1, h2, h3, h4, h5, h6 { color: #89e7ff; } 

    /* Input Fields */
    .stTextInput>div>div>input {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 12px;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #238636; /* GitHub Green */
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #2ea043; }

    /* Info Card */
    .info-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        color: #8b949e;
        margin-bottom: 20px;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #0d1117; border-radius: 6px 6px 0 0; color: #8b949e; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #89e7ff; color: #89e7ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("👻 CodeX: The Ghost Downloader (Masterpiece Edition)")
st.caption("🚀 Ghost Access + Max Quality | Powered by yt-dlp")

if not IS_FFMPEG_READY:
    st.warning("⚠️ ไม่พบ FFmpeg! การรวมไฟล์ภาพและเสียง (1080p+) อาจมีปัญหา แนะนำให้ติดตั้ง FFmpeg ลงในเครื่อง")


# --- 3. Cookies & Input Management ---

with st.expander("🍪 Ghost Access: อัปโหลด Cookies (สำหรับคลิปส่วนตัว/กลุ่มปิด)", expanded=False):
    st.info("💡 ใช้ไฟล์ cookies.txt เพื่อยืนยันตัวตนกับเว็บ (เช่น Facebook, YouTube Premium)")
    uploaded_cookie = st.file_uploader("ลากไฟล์ cookies.txt มาวาง", type=['txt'], key="cookie_ghost")
    
    if uploaded_cookie:
        # สร้างชื่อไฟล์สุ่มเพื่อไม่ให้ชนกัน
        temp_path = os.path.join(DOWNLOAD_FOLDER, f"cookie_{int(time.time())}.txt")
        with open(temp_path, "wb") as f:
            f.write(uploaded_cookie.getbuffer())
        st.session_state.cookie_path = temp_path
        st.success(f"✅ Ghost Access พร้อมใช้งาน!")

# Link Input
url = st.text_input("🔗 วางลิงก์วิดีโอ (YouTube, FB, TikTok, etc.):", placeholder="https://...", key="main_url")


# --- 4. Core Logic Functions (The Missing Pieces) ---

def get_format_string(quality_selection):
    """แปลงตัวเลือก UI เป็นคำสั่ง Format ของ yt-dlp"""
    if "Audio Only" in quality_selection:
        return 'bestaudio/best'
    elif "1080p" in quality_selection:
        return 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
    elif "720p" in quality_selection:
        return 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    else: # Best Available
        return 'bestvideo+bestaudio/best'

def handle_link_generator(video_url, quality):
    """ดึง Direct Link โดยไม่ต้องโหลดไฟล์ลงเครื่อง"""
    format_str = get_format_string(quality)
    
    ydl_opts = {
        'format': format_str,
        'quiet': True,
        'no_warnings': True,
        'user_agent': get_random_user_agent(),
        'skip_download': True, # สำคัญ: ไม่โหลดไฟล์
    }
    
    # ใส่ Cookie ถ้ามี
    if st.session_state.cookie_path and os.path.exists(st.session_state.cookie_path):
        ydl_opts['cookiefile'] = st.session_state.cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # กรณีเป็น Playlist หรือมีหลาย Format
            if 'entries' in info:
                info = info['entries'][0]
                
            return {
                "success": True,
                "title": info.get('title', 'Unknown'),
                "url": info.get('url', None),
                "ext": info.get('ext', 'mp4'),
                "thumbnail": info.get('thumbnail', None)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_server_download(video_url, quality, ffmpeg_ready):
    """ดาวน์โหลดไฟล์ลง Server แล้วส่งให้ user"""
    format_str = get_format_string(quality)
    
    # ตั้งชื่อไฟล์ output
    output_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'user_agent': get_random_user_agent(),
        # ถ้าไม่มี ffmpeg ให้โหลดแบบแยกไฟล์ไม่ได้ (ต้องใช้ best ธรรมดา)
        'merge_output_format': 'mp4' if ffmpeg_ready else None 
    }

    if st.session_state.cookie_path and os.path.exists(st.session_state.cookie_path):
        ydl_opts['cookiefile'] = st.session_state.cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            # หาชื่อไฟล์จริงที่ถูกโหลด
            filename = ydl.prepare_filename(info)
            
            # กรณี yt-dlp เปลี่ยนนามสกุลไฟล์หลัง merge (เช่น .webm -> .mp4)
            if not os.path.exists(filename):
                base, ext = os.path.splitext(filename)
                # ลองเดานามสกุลอื่นที่เป็นไปได้
                for check_ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']:
                    if os.path.exists(base + check_ext):
                        filename = base + check_ext
                        break
            
            return {"success": True, "file_path": filename, "title": info.get('title', 'Video')}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- 5. UI Presentation and Logic ---

tab1, tab2 = st.tabs(["🚀 Quick Link (ดึงลิงก์ตรง)", "💾 Server Download (โหลดลงเครื่อง)"])

# TAB 1: Quick Link Generator
with tab1:
    st.markdown("<div class='info-card'>🚀 <b>Quick Link:</b> ดึงลิงก์ตรง (Direct URL) เพื่อเอาไปเปิดในโปรแกรมอื่น หรือโหลดผ่าน Browser</div>", unsafe_allow_html=True)
    
    q_col1, q_col2 = st.columns([3, 1])
    with q_col1:
        link_quality = st.select_slider("เลือกคุณภาพ:", options=["Audio Only", "720p", "1080p", "Best Available"], value="Best Available")
    with q_col2:
        st.write("") # Spacer
        st.write("")
        gen_btn = st.button("🔍 ดึงลิงก์", type="primary", use_container_width=True)

    if gen_btn and url:
        with st.spinner("👻 กำลังแฝงตัวเข้าไปดึงข้อมูล..."):
            result = handle_link_generator(url, link_quality)
            
            if result["success"]:
                st.success(f"✅ พบวิดีโอ: {result['title']}")
                if result['thumbnail']:
                    st.image(result['thumbnail'], width=300)
                
                st.code(result['url'], language='text')
                st.caption("⚠️ ลิงก์นี้อาจมีอายุใช้งานจำกัด (Expire) ขึ้นอยู่กับเว็บไซต์ต้นทาง")
            else:
                st.error(f"❌ ไม่สามารถดึงลิงก์ได้: {result['error']}")

# TAB 2: Server Download
with tab2:
    st.markdown("<div class='info-card'>💾 <b>Server Download:</b> ระบบจะโหลดไฟล์มาพักไว้ที่ Server ก่อน แล้วให้คุณกด Save ลงเครื่อง (คุณภาพสูงสุด)</div>", unsafe_allow_html=True)
    
    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        server_quality = st.radio("เลือกความละเอียด:", ("Best Available (ชัดสุด)", "1080p", "720p", "Audio Only (MP3/M4A)"), horizontal=True)
    with s_col2:
        st.write("")
        st.write("")
        dl_btn = st.button("🚀 เริ่มดาวน์โหลด", type="primary", use_container_width=True)

    if dl_btn and url:
        with st.spinner("⏳ กำลังดาวน์โหลดและแปลงไฟล์ (อาจใช้เวลาสักครู่)..."):
            result = handle_server_download(url, server_quality, IS_FFMPEG_READY)
            
            if result["success"]:
                file_path = result["file_path"]
                st.success(f"✅ ดาวน์โหลดเสร็จสิ้น: {result['title']}")
                
                # สร้างปุ่ม Download ให้ user กดเซฟไฟล์
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                    st.download_button(
                        label="📥 บันทึกไฟล์ลงเครื่อง",
                        data=file_bytes,
                        file_name=os.path.basename(file_path),
                        mime="application/octet-stream"
                    )
                
                # Clean up (Optional: ลบไฟล์หลังโหลดเสร็จเพื่อประหยัดพื้นที่)
                # os.remove(file_path) 
            else:
                st.error(f"❌ ดาวน์โหลดล้มเหลว: {result['error']}")

# --- Final Cleanup ---
# ลบไฟล์ Cookie เมื่อปิด Session (เพื่อความปลอดภัย)
# หมายเหตุ: ใน Streamlit การ Cleanup แบบ Realtime ทำยาก ส่วนนี้จะทำงานเมื่อมีการ Rerun Script
if st.session_state.cookie_path and not os.path.exists(st.session_state.cookie_path):
    st.session_state.cookie_path = None