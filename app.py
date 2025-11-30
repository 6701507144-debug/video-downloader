import streamlit as st
import yt_dlp
import os
import random
import time
import shutil
import re
import base64

# --- 1. Global Configurations & Utility Functions ---

# โฟลเดอร์เก็บไฟล์ชั่วคราว
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ตรวจสอบ FFmpeg (สำหรับ PC/Server)
FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg.exe"
# ตรวจสอบว่ามีไฟล์ ffmpeg.exe ในโฟลเดอร์ปัจจุบัน หรือ Path ระบบหรือไม่
IS_FFMPEG_READY = os.path.exists(FFMPEG_PATH) or (shutil.which("ffmpeg") is not None)

def get_random_user_agent():
    """Returns a random User-Agent string to mimic a real browser."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
    ]
    return random.choice(user_agents)

# Initialize Session State
if 'download_status' not in st.session_state:
    st.session_state.download_status = None
if 'download_result' not in st.session_state:
    st.session_state.download_result = None
if 'cookie_path' not in st.session_state:
    st.session_state.cookie_path = None

# --- 2. Streamlit UI/UX and CSS Styling ---

st.set_page_config(page_title="CodeX: The Masterpiece Downloader", page_icon="💎", layout="wide")

# Custom CSS for Masterpiece Look
st.markdown("""
<style>
    /* Dark Mode Aesthetic */
    body { color: #ffffff; background-color: #0d1117; }
    h1, h2, h3, h4, h5, h6 { color: #58a6ff; } /* GitHub Blue */

    .stApp { background-color: #0d1117; }
    .main .block-container { padding-top: 2rem; }

    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #161b22; /* Darker background for inputs */
        color: #ffffff;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 10px 12px;
    }

    /* Primary Button (Link Generator) */
    .stButton>button {
        background-color: #2ea44f; /* Green */
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 12px;
        font-weight: bold;
        transition: background-color 0.2s;
    }
    .stButton>button:hover { background-color: #2c974b; }
    
    /* Secondary Button (Server Download) */
    .st-emotion-cache-17lsvqj button { /* Target Secondary button specifically */
        background-color: #58a6ff; /* Blue */
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 12px;
        font-weight: bold;
        transition: background-color 0.2s;
    }
    .st-emotion-cache-17lsvqj button:hover { background-color: #4a90e2; }


    /* Info Card / Box */
    .info-card {
        background-color: #161b22;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
        color: #c9d1d9;
    }
    .small-text { font-size: 0.9em; color: #8b949e; }
    .stAlert.warning { background-color: #58a6ff30; border-left: 5px solid #58a6ff; color: #c9d1d9; }
</style>
""", unsafe_allow_html=True)

# Main Title Section
st.title("💎 CodeX: The Omniversal Masterpiece Downloader")
st.caption("โปรเจกต์ดาวน์โหลดคลิปที่ดีที่สุดในโลก โดย AI โปรแกรมเมอร์")

if not IS_FFMPEG_READY:
    st.warning(f"⚠️ **ไม่พบ FFmpeg!** คุณภาพสูงสุด (1080p+/4K) อาจไม่สามารถรวมภาพ/เสียงได้ ท่านต้องนำ `ffmpeg.exe` ไปวางไว้ใน {os.getcwd()} หรือใน Path ระบบ")
    
# --- 3. Cookies & Input Management ---

with st.expander("🍪 การจัดการ Cookies (สำหรับคลิปกลุ่มปิด/Facebook/Age-restricted)", expanded=False):
    st.info("💡 อัปโหลดไฟล์ cookies.txt ที่นี่ (ไฟล์จะถูกลบทิ้งเมื่อเสร็จงาน)")
    uploaded_cookie = st.file_uploader("ลากไฟล์ cookies.txt มาวาง", type=['txt'], key="cookie_masterpiece")
    
    # Clean up old cookie file if a new one is uploaded or app is reset
    if st.session_state.cookie_path and os.path.exists(st.session_state.cookie_path):
        os.remove(st.session_state.cookie_path)
        st.session_state.cookie_path = None # Reset state

    if uploaded_cookie:
        # Generate a unique path in the downloads folder
        temp_path = os.path.join(DOWNLOAD_FOLDER, f"temp_cookie_{int(time.time())}_{random.randint(100,999)}.txt")
        with open(temp_path, "wb") as f:
            f.write(uploaded_cookie.getbuffer())
        st.session_state.cookie_path = temp_path
        st.success(f"✅ Cookies '{uploaded_cookie.name}' พร้อมใช้งานแล้ว!")

# Link Input
url = st.text_input("🔗 วางลิงก์วิดีโอ (YouTube, Facebook, TikTok, etc.) ที่นี่:", placeholder="ตัวอย่าง: https://www.youtube.com/watch?v=dQw4w9WgXcQ", key="main_url")

# --- 4. Core Logic Functions (Modular Design) ---

def create_ydl_options(selected_format_id, is_server_mode=False):
    """Generates the base yt-dlp options dictionary."""
    opts = {
        'format': selected_format_id,
        'quiet': True,
        'no_warnings': True,
        'user_agent': get_random_user_agent(),
        'nocheckcertificate': True,
        'skip_download': not is_server_mode, # Skip download for Link Generator
    }
    if st.session_state.cookie_path and os.path.exists(st.session_state.cookie_path):
        opts['cookiefile'] = st.session_state.cookie_path
    
    if is_server_mode:
        opts['outtmpl'] = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
    
    return opts

def handle_link_generator(url, link_quality):
    """Logic for the Link Generator tab (Tab 1)."""
    st.session_state.download_status = None
    st.session_state.download_result = None

    if not url:
        st.error("⚠️ กรุณาใส่ลิงก์วิดีโอก่อนครับ")
        return

    status_placeholder = st.empty()
    status_placeholder.info("🕵️‍♂️ กำลังแฮกหาลิงก์ดาวน์โหลดตัวจริง... โปรดรอสักครู่")

    # Define the format string based on user selection
    if link_quality == "Best Available (ชัดสุด)":
        format_str = 'best'
    elif link_quality == "1080p (Full HD)":
        format_str = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
    elif link_quality == "720p (HD)":
        format_str = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
    elif link_quality == "Audio Only (MP3)":
        format_str = 'bestaudio/best'
        
    ydl_opts = create_ydl_options(format_str, is_server_mode=False)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading
            info = ydl.extract_info(url, download=False)
            
            video_url = info.get('url') # Try to get the direct URL yt-dlp chose
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail', '')
            
            # Additional logic to find the best direct link (especially for combined formats)
            if not video_url and info.get('formats'):
                for f in info.get('formats', []):
                    # Prioritize formats that contain both video and audio (if available)
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                        video_url = f['url']
                        break
                # Fallback: take the first non-None URL
                if not video_url:
                    for f in info.get('formats', []):
                        if f.get('url'):
                            video_url = f['url']
                            break

        if video_url:
            st.session_state.download_status = "success"
            st.session_state.download_result = {
                'url': video_url,
                'title': title,
                'thumbnail': thumbnail,
                'duration': info.get('duration_string', 'N/A'),
                'uploader': info.get('uploader', 'N/A'),
            }
            status_placeholder.empty()
        else:
            st.session_state.download_status = "error"
            st.session_state.download_result = "ไม่พบลิงก์ตรงที่เหมาะสม ลองเลือกคุณภาพอื่น หรือใช้โหมด Server ดูครับ"
            status_placeholder.empty()

    except yt_dlp.DownloadError as e:
        st.session_state.download_status = "error"
        st.session_state.download_result = f"❌ Error: {e}"
        status_placeholder.empty()
    except Exception as e:
        st.session_state.download_status = "error"
        st.session_state.download_result = f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}"
        status_placeholder.empty()


def handle_server_download(url, server_quality, IS_FFMPEG_READY):
    """Logic for the Server Download tab (Tab 2)."""
    st.session_state.download_status = None
    st.session_state.download_result = None
    
    if not url:
        st.error("⚠️ กรุณาใส่ลิงก์วิดีโอก่อนครับ")
        return 

    status_placeholder_server = st.empty()
    progress_bar = st.progress(0)
    
    # 1. Define Format String and check FFMPEG
    format_str = 'best'
    
    if server_quality == "Best (4K/8K ถ้ามี)":
        if IS_FFMPEG_READY: format_str = 'bestvideo+bestaudio/best'
        else: st.error("❌ โหมดนี้ต้องการ FFmpeg"); return
    elif server_quality == "1080p (Full HD)":
        if IS_FFMPEG_READY: format_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        else: st.error("❌ โหมดนี้ต้องการ FFmpeg"); return
    elif server_quality == "720p (HD)":
        format_str = 'best[ext=mp4][height<=720]/best[ext=mp4]/best'
    elif server_quality == "Audio Only (MP3)":
        format_str = 'bestaudio/best'

    ydl_opts = create_ydl_options(format_str, is_server_mode=True)
    
    # Progress Hook for Real-time update
    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                p_match = re.search(r'(\d+\.?\d*)%', d.get('_percent_str', '0%'))
                p_str = p_match.group(1) if p_match else '0'
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                
                if p_str.replace('.', '', 1).isdigit():
                    progress_bar.progress(int(float(p_str)))
                    status_placeholder_server.info(f"⚡ กำลังโหลด: {p_str}% | Speed: {speed} | ETA: {eta}")
            except Exception:
                pass
        elif d['status'] == 'finished':
            progress_bar.progress(100)
            status_placeholder_server.success("✅ ดาวน์โหลดเสร็จสิ้น! กำลังรวมไฟล์...")
            
    ydl_opts['progress_hooks'] = [progress_hook]
    
    # 2. Start Download
    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            status_placeholder_server.info("🔥 เริ่มดาวน์โหลดและรวมไฟล์...")
            info = ydl.extract_info(url, download=True)
            
            # Prepare filename, handling combined formats
            filename = ydl.prepare_filename(info)
            
            # Check if the file name is correct after post-processing/combining
            if not os.path.exists(filename):
                # Search for the final file name in the DOWNLOAD_FOLDER
                base = os.path.splitext(filename)[0]
                for f in os.listdir(DOWNLOAD_FOLDER):
                    full_path = os.path.join(DOWNLOAD_FOLDER, f)
                    if base in full_path and os.path.exists(full_path):
                        filename = full_path
                        break
        
        if os.path.exists(filename):
            st.session_state.download_status = "server_success"
            st.session_state.download_result = {'filename': filename}
        else:
            raise FileNotFoundError("ไม่พบไฟล์ที่สร้างขึ้นหลังดาวน์โหลดเสร็จสมบูรณ์")


    except yt_dlp.DownloadError as e:
        st.session_state.download_status = "error"
        st.session_state.download_result = f"❌ yt-dlp Error: {e}"
    except Exception as e:
        st.session_state.download_status = "error"
        st.session_state.download_result = f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}"
    finally:
        progress_bar.empty()
        status_placeholder_server.empty()
        # Clean up any unsuccessful downloads (if filename exists, it will be handled by the success logic)
        if st.session_state.download_status != "server_success" and filename and os.path.exists(filename):
             os.remove(filename)


# --- 5. UI Presentation and Tab Logic ---

tab1, tab2 = st.tabs(["🚀 Link Generator (แนะนำ)", "💾 Server Download (สำรอง)"])

# -----------------
# TAB 1: Link Generator
# -----------------
with tab1:
    st.markdown("<div class='info-card'><p>🚀 <b>Link Generator:</b> Server จะ **'ขุดหาลิงก์ตรง'** มาให้คุณคลิกโหลดเองทันที นี่คือวิธีที่ **เร็วที่สุดและเสถียรที่สุด**</p><p class='small-text'>แนะนำให้ใช้โหมดนี้เป็นอันดับแรก</p></div>", unsafe_allow_html=True)
    
    st.markdown("<h5>เลือกคุณภาพที่ต้องการสำหรับลิงก์ตรง:</h5>", unsafe_allow_html=True)
    link_quality = st.radio(" ", 
        ("Best Available (ชัดสุด)", "1080p (Full HD)", "720p (HD)", "Audio Only (MP3)"),
        key='link_gen_quality_radio') 

    if st.button("🔍 ขุดลิงก์ดาวน์โหลด (Generate Link)", type="primary", use_container_width=True):
        handle_link_generator(url, link_quality)
        
    # --- Result Display (Link Generator) ---
    if st.session_state.download_status == "success":
        result = st.session_state.download_result
        st.success("✅ พบลิงก์ดาวน์โหลดแล้ว!")
        st.subheader(f"🎬 {result['title']}")
        st.markdown(f"<small>จาก: {result['uploader']} | ความยาว: {result['duration']}</small>", unsafe_allow_html=True)
        
        if result['thumbnail']:
            st.image(result['thumbnail'], width=300, caption="Thumbnail")

        # Beautiful download link/button
        st.markdown(f"""
            <a href="{result['url']}" target="_blank" style="text-decoration:none;">
                <button style="background-color: #ff4b4b; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer; width: 100%;">
                    ⬇️ คลิกที่นี่เพื่อเริ่มดาวน์โหลดทันที
                </button>
            </a>
            <p class='small-text'>*หากคลิกแล้ววิดีโอเล่นอัตโนมัติ ให้คลิกขวาที่วิดีโอ (หรือกดค้างบนมือถือ) แล้วเลือก 'Save Video As...'</p>
        """, unsafe_allow_html=True)
        st.text_area("หรือคัดลอกลิงก์ตรงนี้ (สำหรับ IDM/โปรแกรมอื่น):", value=result['url'], height=100)

    elif st.session_state.download_status == "error":
        st.error(st.session_state.download_result)

# -----------------
# TAB 2: Server Download
# -----------------
with tab2:
    st.markdown("<div class='info-card'><p>💾 <b>Server Download:</b> Server จะดาวน์โหลดไฟล์มา **รวมภาพ+เสียง** และส่งให้คุณเป็นไฟล์เดียว</p><p class='small-text'>เหมาะสำหรับคลิปคุณภาพสูง (1080p+/4K) หรือเมื่อ Link Generator ใช้ไม่ได้</p></div>", unsafe_allow_html=True)
    
    st.markdown("<h5>เลือกคุณภาพที่ต้องการ (ต้องการ FFmpeg สำหรับการรวมไฟล์):</h5>", unsafe_allow_html=True)
    server_quality = st.radio(" ", 
        ("Best (4K/8K ถ้ามี)", "1080p (Full HD)", "720p (HD - ปลอดภัย)", "Audio Only (MP3)"),
        key='server_download_quality_radio')
    
    if st.button("🚀 เริ่มดาวน์โหลดผ่าน Server", type="secondary", use_container_width=True):
        handle_server_download(url, server_quality, IS_FFMPEG_READY)

    # --- Result Display (Server Download) ---
    if st.session_state.download_status == "server_success":
        filename = st.session_state.download_result['filename']
        st.success("✅ ดาวน์โหลดและรวมไฟล์สำเร็จ! คลิกปุ่มด้านล่างเพื่อรับไฟล์")
        
        # Ensure file exists before reading
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                st.download_button("⬇️ รับไฟล์เข้าเครื่อง", 
                                   f, 
                                   file_name=os.path.basename(filename), 
                                   mime="application/octet-stream", 
                                   use_container_width=True)
            
            st.info("ไฟล์จะถูกลบออกจาก Server เพื่อประหยัดพื้นที่หลังการดาวน์โหลด")
            
            # Clean up the file after offering the download button
            try:
                os.remove(filename)
                st.session_state.download_status = None # Reset status after cleanup
            except Exception as e:
                st.warning(f"❌ ไม่สามารถลบไฟล์ชั่วคราวได้: {e}")
        else:
            st.error("❌ ไฟล์ต้นฉบับหายไปจาก Server")
            st.session_state.download_status = None # Reset
            
    elif st.session_state.download_status == "error":
        st.error(st.session_state.download_result)

# --- Final Cleanup (Execute once per run cycle) ---
# Clean up temporary cookie file in the session state
if st.session_state.cookie_path and os.path.exists(st.session_state.cookie_path):
    st.info("กำลังลบไฟล์ Cookies ชั่วคราว...")
    try:
        os.remove(st.session_state.cookie_path)
    except Exception:
        pass
    st.session_state.cookie_path = None