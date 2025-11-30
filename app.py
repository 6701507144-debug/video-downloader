import streamlit as st
import yt_dlp
import os
import shutil
import time
import subprocess 
import random 
import re # สำหรับใช้ตรวจสอบ path

# --- 1. การตั้งค่าหน้าเว็บและการออกแบบ UI (CSS Global Styling) ---
st.set_page_config(page_title="CodeX: Omniversal Downloader", page_icon="💎", layout="wide")

# Custom CSS for a modern, clean, and interactive UI
st.markdown("""
<style>
    /* General Font and Background */
    body { font-family: 'Segoe UI', sans-serif; background-color: #f0f2f6; color: #333; }
    h1, h2, h3, h4, h5, h6 { color: #2e8b57; } /* SeaGreen for headers */

    /* Main Container */
    .stApp {
        background-color: #f0f2f6;
        padding-top: 20px;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    /* Input Fields */
    .stTextInput>div>div>input {
        border-radius: 0.5rem;
        border: 1px solid #ccc;
        padding: 0.75rem 1rem;
        font-size: 1.1rem;
    }
    .stTextArea>div>div>textarea {
        border-radius: 0.5rem;
        border: 1px solid #ccc;
        padding: 0.75rem 1rem;
        font-size: 1.1rem;
    }

    /* Buttons */
    .stButton>button {
        background-color: #2e8b57; /* SeaGreen */
        color: white;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: bold;
        border: none;
        transition: background-color 0.2s;
    }
    .stButton>button:hover {
        background-color: #24804c; /* Darker SeaGreen on hover */
        color: white;
    }
    .stDownloadButton>button { /* For download button */
        background-color: #1e90ff; /* DodgerBlue */
        color: white;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: bold;
        border: none;
        transition: background-color 0.2s;
    }
    .stDownloadButton>button:hover {
        background-color: #1a7ae0; /* Darker DodgerBlue */
        color: white;
    }

    /* Expander / Sidebar */
    .streamlit-expanderHeader {
        background-color: #e0f2f7; /* Light Blue */
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: bold;
        color: #007bff; /* Blue text */
    }
    .streamlit-expanderContent {
        background-color: #ffffff;
        border-radius: 0.5rem;
        padding: 1rem;
        border: 1px solid #eee;
    }

    /* Status Messages */
    .stAlert {
        border-radius: 0.5rem;
        font-size: 1rem;
        padding: 1rem;
    }
    .stAlert.info { background-color: #e6f7ff; border-left: 5px solid #007bff; color: #004085; }
    .stAlert.success { background-color: #e6ffed; border-left: 5px solid #28a745; color: #155724; }
    .stAlert.warning { background-color: #fff3e6; border-left: 5px solid #ffc107; color: #856404; }
    .stAlert.error { background-color: #ffe6e6; border-left: 5px solid #dc3545; color: #721c24; }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: #2e8b57; /* SeaGreen */
    }

    /* Custom Cards for Info */
    .info-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .small-text {
        font-size: 0.85em;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

st.title("💎 CodeX: The Omniversal Downloader")
st.caption("โปรเจกต์ดาวน์โหลดคลิปที่ดีที่สุดในโลก โดย AI โปรแกรมเมอร์")

# --- 2. การตั้งค่าเบื้องต้นและโฟลเดอร์ ---
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ตรวจสอบ FFmpeg (สำหรับ PC)
FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg.exe"
IS_FFMPEG_READY = os.path.exists(FFMPEG_PATH) or (shutil.which("ffmpeg") is not None)

if not IS_FFMPEG_READY:
    st.warning("⚠️ ไม่พบ FFmpeg! คุณภาพสูง (1080p+/4K) อาจไม่สามารถรวมภาพ/เสียงได้")
    st.markdown("ถ้าต้องการโหลดคุณภาพสูง: [📥 ดาวน์โหลด FFmpeg ที่นี่ (สำหรับ Windows)](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip) แล้วนำ `ffmpeg.exe` ไปวางไว้ข้าง `app.py`")

# --- 3. ฟังก์ชันสุ่ม User Agent ---
def get_random_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
    ]
    return random.choice(user_agents)

# --- 4. ระบบจัดการ Cookies (สำหรับ Private Content / Facebook) ---
cookie_path = None
with st.expander("🍪 Cookies & Authentication (สำหรับคลิปกลุ่มปิด/Facebook/Age-restricted)", expanded=False):
    st.info("💡 หากโหลดไม่ได้ หรือติด 'Login Required' ให้อัปโหลดไฟล์ cookies.txt ที่นี่")
    uploaded_cookie = st.file_uploader("ลากไฟล์ cookies.txt มาวาง (จะถูกลบทิ้งเมื่อเสร็จงาน)", type=['txt'])
    
    if uploaded_cookie:
        # สร้างชื่อไฟล์ชั่วคราวที่ไม่ซ้ำกัน
        cookie_path = f"temp_cookie_{int(time.time())}_{random.randint(100,999)}.txt"
        with open(cookie_path, "wb") as f:
            f.write(uploaded_cookie.getbuffer())
        st.success(f"✅ Cookies '{uploaded_cookie.name}' พร้อมใช้งาน!")

# --- 5. ส่วนรับ Link URL ---
url = st.text_input("🔗 วางลิงก์วิดีโอ (YouTube, Facebook, TikTok, etc.) ที่นี่:", placeholder="ตัวอย่าง: https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# --- 6. แท็บเลือกโหมดการทำงาน ---
tab1, tab2 = st.tabs(["🚀 โหมด Link Generator (แนะนำ)", "💾 โหมดดาวน์โหลดผ่าน Server (สำรอง)"])


# --- 7. ฟังก์ชันจัดการดาวน์โหลดผ่าน Server (สำหรับ Tab 2) ---
def handle_server_download(url, server_quality, cookie_path, IS_FFMPEG_READY):
    # ตรวจสอบ URL
    if not url:
        st.error("⚠️ กรุณาใส่ลิงก์วิดีโอก่อนครับ")
        return # return ในฟังก์ชันนี้ใช้ได้
    
    # Global variables required in function scope
    DOWNLOAD_FOLDER = "downloads"
    
    # Placeholders for dynamic updates
    status_placeholder_server = st.empty()
    progress_bar = st.progress(0)
    
    # progress_hook สำหรับอัปเดตสถานะแบบ Real-time
    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                # ใช้ RegEx เพื่อดึงเปอร์เซ็นต์อย่างปลอดภัย
                p_match = re.search(r'(\d+\.?\d*)%', d.get('_percent_str', '0%'))
                p_str = p_match.group(1) if p_match else '0'
                
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                if p_str.replace('.', '', 1).isdigit():
                    progress_bar.progress(int(float(p_str)))
                    status_placeholder_server.info(f"⚡ กำลังโหลด: {p_str}% | Speed: {speed} | ETA: {eta}")
            except ValueError:
                pass # Ignore if percent_str is not a valid number
        elif d['status'] == 'finished':
            progress_bar.progress(100)
            status_placeholder_server.success("✅ ดาวน์โหลดเสร็จสิ้น! กำลังรวมไฟล์...")

    ydl_opts_server = {
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'user_agent': get_random_user_agent(),
        'nocheckcertificate': True,
        'progress_hooks': [progress_hook], 
    }
    if cookie_path: ydl_opts_server['cookiefile'] = cookie_path
    
    # กำหนด format ตามคุณภาพที่เลือก (Logic ที่มี return ถูกย้ายมาที่นี่)
    if server_quality == "Best (4K/8K ถ้ามี - ต้องมี FFmpeg)":
        if IS_FFMPEG_READY: ydl_opts_server['format'] = 'bestvideo+bestaudio/best'
        else: st.error("❌ โหมดนี้ต้องมี FFmpeg ครับ"); return
    elif server_quality == "1080p (Full HD - ต้องมี FFmpeg)":
        if IS_FFMPEG_READY: ydl_opts_server['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        else: st.error("❌ โหมดนี้ต้องมี FFmpeg ครับ"); return
    elif server_quality == "720p (HD - ปลอดภัย)":
        ydl_opts_server['format'] = 'best[ext=mp4][height<=720]/best[ext=mp4]/best'
    elif server_quality == "Audio Only (MP3)":
        ydl_opts_server['format'] = 'bestaudio/best'
        if IS_FFMPEG_READY: ydl_opts_server['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192',}]
        else: st.warning("💡 ไม่มี FFmpeg จะได้ไฟล์เสียงนามสกุล .webm/.m4a แทน MP3 ครับ")

    # ส่วน Try/Except ที่เหลือ (Logic โหลดไฟล์จริง)
    try:
        with yt_dlp.YoutubeDL(ydl_opts_server) as ydl:
            status_placeholder_server.info("🔥 เริ่มดาวน์โหลดและรวมไฟล์...")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Fix: บางทีชื่อไฟล์เปลี่ยน
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                for f in os.listdir(DOWNLOAD_FOLDER):
                    # ต้องรวม path เต็มก่อนเปรียบเทียบ
                    full_path = os.path.join(DOWNLOAD_FOLDER, f)
                    if base in full_path:
                        filename = full_path
                        break
        
        # ตรวจสอบว่าไฟล์ถูกสร้างขึ้นจริงหรือไม่
        if not os.path.exists(filename):
            raise FileNotFoundError(f"ไม่พบไฟล์ที่ถูกสร้าง: {filename}")
            
        status_placeholder_server.success("✅ ดาวน์โหลดเสร็จสมบูรณ์! คลิกปุ่มด้านล่างเพื่อรับไฟล์")
        st.markdown("---")
        with open(filename, "rb") as f:
            st.download_button("⬇️ รับไฟล์เข้าเครื่อง", f, file_name=os.path.basename(filename), mime="application/octet-stream", use_container_width=True)
        
        # ลบไฟล์
        st.info("ไฟล์จะถูกลบออกจาก Server เพื่อประหยัดพื้นที่")
        os.remove(filename)

    except yt_dlp.DownloadError as e:
        status_placeholder_server.error(f"❌ yt-dlp Error: {e}")
        if "age-restricted" in str(e).lower() or "login" in str(e).lower():
            st.warning("💡 คลิปนี้อาจถูกจำกัดอายุ/ต้องเข้าสู่ระบบ ลองอัปโหลด Cookies ดูครับ")
        elif "Private video" in str(e):
            st.warning("💡 คลิปนี้เป็นส่วนตัว ลองอัปโหลด Cookies ดูครับ")
        elif "403 Forbidden" in str(e):
            st.warning("💡 Server อาจโดนบล็อก IP ลองอัปโหลด Cookies ดูครับ")
    except Exception as e:
        status_placeholder_server.error(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
    finally:
        progress_bar.empty()
        status_placeholder_server.empty()
        
# ==========================================
# 📍 TAB 1: Link Generator (เร็วที่สุด) - โค้ดเดิม
# ==========================================
with tab1:
    st.markdown("<div class='info-card'><p>🚀 <b>โหมด Link Generator:</b> Server จะไม่ดาวน์โหลดไฟล์ แต่จะ <b>'ขุดหาลิงก์ตรง'</b> ของวิดีโอมาให้คุณคลิกโหลดเองทันที</p><p class='small-text'>นี่คือวิธีที่เร็วที่สุดเพราะไม่ต้องเสียเวลาประมวลผลบน Server ของเรา</p></div>", unsafe_allow_html=True)
    
    st.markdown("<h5>เลือกคุณภาพที่ต้องการสำหรับลิงก์ตรง:</h5>", unsafe_allow_html=True)
    link_quality = st.radio(" ", 
        ("Best Available (ชัดสุด)", "1080p (Full HD)", "720p (HD)", "Audio Only (MP3)"),
        key='link_gen_quality_radio') 

    if st.button("🔍 ขุดลิงก์ดาวน์โหลด (Generate Link)", use_container_width=True):
        if not url:
            st.error("⚠️ กรุณาใส่ลิงก์วิดีโอก่อนครับ")
        else:
            status_placeholder = st.empty()
            status_placeholder.info("🕵️‍♂️ กำลังแฮกหาลิงก์ดาวน์โหลดตัวจริง... โปรดรอสักครู่")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'user_agent': get_random_user_agent(),
                'nocheckcertificate': True, 
                'format': 'best', 
            }
            if cookie_path: ydl_opts['cookiefile'] = cookie_path

            if link_quality == "1080p (Full HD)":
                ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
            elif link_quality == "720p (HD)":
                ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
            elif link_quality == "Audio Only (MP3)":
                ydl_opts['format'] = 'bestaudio/best'
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    video_url = None
                    title = info.get('title', 'Unknown Title')
                    thumbnail = info.get('thumbnail', '')
                    duration = info.get('duration_string', 'N/A')
                    uploader = info.get('uploader', 'N/A')

                    if link_quality == "Audio Only (MP3)":
                        # Logic for audio only
                        for f in info.get('formats', []):
                            if f.get('acodec') != 'none':
                                video_url = f['url']
                                break
                    else:
                        # Logic for combined video/audio (or best available link)
                        for f in info.get('formats', []):
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                                if (link_quality == "1080p (Full HD)" and f.get('height') <= 1080) or \
                                   (link_quality == "720p (HD)" and f.get('height') <= 720) or \
                                   (link_quality == "Best Available"):
                                    video_url = f['url']
                                    break 

                        if not video_url and info.get('url'): # Fallback to info['url']
                            video_url = info['url']
                        
                        # Fallback for streams where image and audio are separated (yt-dlp needs FFmpeg but Link Generator aims for single link)
                        if not video_url and info.get('formats'):
                             for f in info.get('formats', []):
                                if f.get('url') and f.get('vcodec') != 'none':
                                    video_url = f['url']
                                    break # Try to get the best video link


                    if video_url:
                        status_placeholder.success("✅ พบลิงก์ดาวน์โหลดแล้ว!")
                        st.subheader(f"🎬 {title}")
                        st.markdown(f"<small>จาก: {uploader} | ความยาว: {duration}</small>", unsafe_allow_html=True)
                        if thumbnail:
                            st.image(thumbnail, width=300, caption="Thumbnail")

                        st.markdown(f"""
                            <a href="{video_url}" target="_blank" class="big-btn" style="text-decoration:none;">
                                <button style="background-color: #28a745; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer;">
                                    ⬇️ คลิกที่นี่เพื่อเริ่มดาวน์โหลดทันที
                                </button>
                            </a>
                            <p class='small-text'>*หากคลิกแล้ววิดีโอเล่นอัตโนมัติ ให้คลิกขวาที่วิดีโอ (หรือกดค้างบนมือถือ) แล้วเลือก 'Save Video As...'</p>
                        """, unsafe_allow_html=True)
                        st.markdown("---")
                        st.text_area("หรือคัดลอกลิงก์ตรงนี้ (สำหรับ IDM/โปรแกรมอื่น):", value=video_url, height=100)
                    else:
                        status_placeholder.error("❌ ไม่พบลิงก์ดาวน์โหลดที่เหมาะสม ลองเลือกคุณภาพอื่น หรือใช้โหมด Server ดูครับ")

            except yt_dlp.DownloadError as e:
                status_placeholder.error(f"❌ yt-dlp Error: {e}")
                if "age-restricted" in str(e).lower() or "login" in str(e).lower() or "403" in str(e):
                    st.warning("💡 คลิปนี้อาจถูกจำกัดอายุ/ต้องเข้าสู่ระบบ ลองอัปโหลด Cookies ดูครับ")
                elif "Private video" in str(e):
                    st.warning("💡 คลิปนี้เป็นส่วนตัว ลองอัปโหลด Cookies ดูครับ")
            except Exception as e:
                status_placeholder.error(f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")

# ==========================================
# 📍 TAB 2: Server Download (สำรอง & สำหรับ PC) - โค้ดเดิม
# ==========================================
with tab2:
    st.markdown("<div class='info-card'><p>💾 <b>โหมดดาวน์โหลดผ่าน Server:</b> Server ของเราจะดาวน์โหลดไฟล์วิดีโอมาเก็บไว้ชั่วคราว แล้วส่งให้คุณเป็นไฟล์</p><p class='small-text'>โหมดนี้เหมาะสำหรับ: <b>PC ของคุณเอง (แรงกว่า)</b> หรือใช้เป็นตัวเลือกสำรองเมื่อโหมด Link Generator ไม่ได้ผล</p></div>", unsafe_allow_html=True)
    
    st.markdown("<h5>เลือกคุณภาพที่ต้องการ (ต้องมี FFmpeg สำหรับ 1080p/4K):</h5>", unsafe_allow_html=True)
    server_quality = st.radio(" ", 
        ("Best (4K/8K ถ้ามี - ต้องมี FFmpeg)", "1080p (Full HD - ต้องมี FFmpeg)", "720p (HD - ปลอดภัย)", "Audio Only (MP3)"),
        key='server_download_quality_radio')

    if st.button("🚀 เริ่มดาวน์โหลดผ่าน Server", use_container_width=True):
        # เรียกฟังก์ชันใหม่ พร้อมส่งตัวแปรที่จำเป็นเข้าไป
        handle_server_download(url, server_quality, cookie_path, IS_FFMPEG_READY)
        
# --- Cleanup Cookies (ลบไฟล์ Cookies ชั่วคราวหลังใช้งาน) ---
# ทำความสะอาดไฟล์ Cookies ชั่วคราว (ถ้ามีการอัปโหลด)
if cookie_path and os.path.exists(cookie_path):
    try:
        os.remove(cookie_path)
        # st.sidebar.info("ลบไฟล์ Cookies ชั่วคราวเรียบร้อยแล้ว") # Comment out this line to avoid unnecessary sidebar update
    except Exception:
        pass # Ignore errors during cleanup