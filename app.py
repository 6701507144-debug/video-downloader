import streamlit as st
import yt_dlp
import os
import time

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Cloud Downloader", page_icon="☁️", layout="centered")
st.title("☁️ Cloud Video Downloader")
st.caption("Server-side Downloader: โหลดลงเซิร์ฟเวอร์ -> ส่งเข้ามือถือคุณ")

# สร้างโฟลเดอร์เก็บไฟล์ชั่วคราว
download_folder = "downloads"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# --- 2. ส่วนอัปโหลด Cookies (Optional) ---
# หมายเหตุ: บน Cloud ห้ามเอาไฟล์ cookies.txt ขึ้น GitHub เด็ดขาด (อันตราย) ให้ใช้วิธีอัปโหลดหน้าเว็บแบบนี้ปลอดภัยสุด
with st.expander("🍪 ตั้งค่า Cookies (สำหรับกลุ่มปิด/เฟสบุ๊ค)"):
    uploaded_cookie = st.file_uploader("ลากไฟล์ cookies.txt มาวางตรงนี้", type=['txt'])
    cookie_path = None
    if uploaded_cookie:
        cookie_path = f"temp_cookie_{int(time.time())}.txt"
        with open(cookie_path, "wb") as f:
            f.write(uploaded_cookie.getbuffer())
        st.success("✅ Cookies พร้อม!")

# --- 3. รับลิงก์ ---
url = st.text_input("🔗 Link URL:")
mode = st.radio("เลือกโหมด:", ("Video Normal", "Audio Only (MP3)"))

# --- 4. ฟังก์ชันโหลด ---
def download_and_send():
    if not url:
        st.warning("⚠️ ใส่ลิงก์ก่อนครับ")
        return

    status_text = st.empty()
    status_text.info("⏳ Server กำลังดาวน์โหลดจากเว็บต้นทาง... (รอแป๊บนึง)")
    
    # ตั้งค่า yt-dlp
    ydl_opts = {
        'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # บังคับ User Agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path

    if mode == "Audio Only (MP3)":
        ydl_opts['format'] = 'bestaudio/best'
        # บน Cloud การแปลงไฟล์อาจมีปัญหาเรื่อง FFmpeg ในบางครั้ง
        # เวอร์ชั่นนี้จะพยายามโหลดไฟล์เสียงที่ดีที่สุดมาเลย
    else:
        ydl_opts['format'] = 'best'

    try:
        # เริ่มโหลดลง Server
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # แก้ชื่อไฟล์ให้ถูกต้อง (บางที yt-dlp เปลี่ยนนามสกุลเอง)
            if not os.path.exists(filename):
                # ลองหาไฟล์ใกล้เคียง
                base = os.path.splitext(filename)[0]
                for f in os.listdir(download_folder):
                    if base in os.path.join(download_folder, f):
                        filename = os.path.join(download_folder, f)
                        break
            
        status_text.success("✅ Server โหลดเสร็จแล้ว! กดปุ่มด้านล่างเพื่อรับไฟล์")
        
        # --- ไฮไลท์: ปุ่มส่งไฟล์เข้ามือถือ ---
        with open(filename, "rb") as f:
            btn = st.download_button(
                label="⬇️ Download เข้ามือถือคลิกที่นี่",
                data=f,
                file_name=os.path.basename(filename),
                mime="application/octet-stream"
            )
            
    except Exception as e:
        status_text.error(f"❌ Error: {e}")

    # ล้างไฟล์ Cookie ชั่วคราว
    if cookie_path and os.path.exists(cookie_path):
        os.remove(cookie_path)

if st.button("🚀 Start Cloud Process"):
    download_and_send()