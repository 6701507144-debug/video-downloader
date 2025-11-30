import streamlit as st
import yt_dlp
import os
import time

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="PC Master Downloader", page_icon="💻", layout="wide")
st.title("💻 PC High-Performance Downloader")
st.caption("โหมดประสิทธิภาพสูง: Multi-thread + FFmpeg (4K/8K Ready)")

# โฟลเดอร์เก็บไฟล์
download_folder = "downloads"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# --- 2. ตั้งค่า Cookies (สำหรับเฟส/กลุ่มปิด) ---
with st.expander("🍪 ตั้งค่า Cookies (ใช้ไฟล์ในเครื่องได้เลย)"):
    # บน PC เราสามารถเลือกไฟล์จากเครื่องได้ง่ายๆ หรือจะพิมพ์ชื่อไฟล์ก็ได้
    cookie_file = st.text_input("ระบุชื่อไฟล์ Cookies (เช่น fb.txt):", value="cookies.txt")
    
    # เช็คว่ามีไฟล์จริงไหม
    has_cookie = os.path.exists(cookie_file)
    if has_cookie:
        st.success(f"✅ ตรวจพบไฟล์: {cookie_file} พร้อมใช้งาน!")
    else:
        st.warning("⚠️ ยังไม่พบไฟล์ Cookies ในโฟลเดอร์ (ถ้าจะโหลด Private ต้องมี)")

# --- 3. ส่วนรับลิงก์ ---
col1, col2 = st.columns([3, 1])
with col1:
    url = st.text_input("🔗 Link URL:")
with col2:
    # เลือกความละเอียด (บน PC เอาให้สุด)
    res_option = st.selectbox("คุณภาพ:", 
        ("Best Available (ชัดสุดที่มี 4K/8K)", 
         "1080p (Full HD)", 
         "720p (HD - โหลดไว)", 
         "Audio Only (MP3)"))

# --- 4. ฟังก์ชันโหลดแบบ Turbo PC ---
def download_pc():
    if not url:
        st.warning("⚠️ ใส่ลิงก์ก่อนครับ")
        return

    status_box = st.info("🚀 กำลังเริ่มระบบ Multi-thread...")
    progress_bar = st.progress(0)
    
    # ฟังก์ชันสำหรับอัปเดตหลอดโหลด (Hook)
    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                # คำนวณเปอร์เซ็นต์
                p = d.get('_percent_str', '0%').replace('%','')
                progress_bar.progress(float(p) / 100)
                status_box.write(f"⚡ Speed: {d.get('_speed_str')} | ETA: {d.get('_eta_str')}")
            except:
                pass
        elif d['status'] == 'finished':
            status_box.success("✅ ดาวน์โหลดเสร็จสิ้น! กำลังรวมไฟล์ (Merge)...")
            progress_bar.progress(100)

    # --- การตั้งค่าที่แรงที่สุด (Optimized for PC) ---
    ydl_opts = {
        'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
        
        # 1. เปิดท่อดูด 8 ท่อพร้อมกัน (เหมือน IDM)
        'concurrent_fragment_downloads': 8,
        
        # 2. ตั้งค่า Buffer ให้เขียนลง Disk ไวขึ้น
        'buffersize': 1024 * 1024, # 1MB buffer
        'retries': 10, # ถ้าเน็ตหลุด ให้ลองใหม่ 10 รอบ
        'fragment_retries': 10,

        # 3. บอกตำแหน่ง FFmpeg (ถ้าใส่ไว้ในโฟลเดอร์เดียวกัน)
        'ffmpeg_location': os.getcwd(),
        
        # ปลอมตัวเนียนๆ
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # ใส่ Cookies
    if has_cookie:
        ydl_opts['cookiefile'] = cookie_file

    # เลือกคุณภาพ
    if res_option == "Audio Only (MP3)":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320',}]
    
    elif res_option == "1080p (Full HD)":
        # เลือกชัดสุดที่ไม่เกิน 1080p + เสียงที่ดีที่สุด
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
    
    elif res_option == "720p (HD - โหลดไว)":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        
    else: # Best Available
        # เอาชัดสุดเท่าที่มีในโลก (4K/8K)
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    # เริ่มโหลด
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            
        st.balloons()
        status_box.success(f"🎉 เรียบร้อย! ไฟล์อยู่ในโฟลเดอร์: {os.path.abspath(download_folder)}")
        
    except Exception as e:
        status_box.error(f"❌ Error: {e}")
        st.error("💡 ถ้าโหลดคุณภาพสูงไม่ได้ เช็คว่ามีไฟล์ ffmpeg.exe ในโฟลเดอร์หรือยัง?")

# ปุ่มกด
if st.button("🚀 IGNITE DOWNLOAD (PC POWER)", type="primary"):
    download_pc()