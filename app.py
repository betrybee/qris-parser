import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
from PIL import Image
from pyzbar.pyzbar import decode

st.set_page_config(page_title="QRIS Parser", page_icon="🔍", layout="centered")

# Inisialisasi koneksi Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(worksheet="Sheet1", ttl=0)
        data = data.dropna(how="all")
        return data
    except Exception:
        return pd.DataFrame(columns=["Timestamp", "Username", "Filename"])

df_logs = load_data()
total_counter = len(df_logs)

st.title("🔍 QRIS Parser App")
st.write("Aplikasi untuk mengekstrak dan membaca informasi detail dari gambar QRIS.")

# Tampilkan metrik statistik penggunaan
st.metric(label="📊 Total QRIS Diproses", value=f"{total_counter} Kali")

st.divider()

username = st.text_input("Username / Nama Pengguna", placeholder="Masukkan nama/username Anda...")
uploaded_file = st.file_uploader("Unggah Gambar QRIS (JPG, PNG, JPEG)", type=["jpg", "jpeg", "png"])

if st.button("Parse QRIS", type="primary"):
    if not username.strip():
        st.error("⚠️ Silakan isi Username Anda terlebih dahulu sebelum memproses.")
    elif uploaded_file is None:
        st.error("⚠️ Silakan unggah gambar QRIS terlebih dahulu.")
    else:
        with st.spinner("Membaca dan memproses QRIS..."):
            try:
                # 1. Dekode Gambar QRIS
                img = Image.open(uploaded_file)
                decoded_objects = decode(img)
                
                if decoded_objects:
                    qr_data = decoded_objects[0].data.decode('utf-8')
                    
                    # Tampilkan Hasil Parsing QRIS ke Layar
                    st.success(f"✅ QRIS Berhasil Diproses untuk **{username}**!")
                    st.subheader("📌 Raw Payload QRIS:")
                    st.code(qr_data, language="text")
                    
                    # 2. Simpan Log ke Google Sheets
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_log = pd.DataFrame([{
                        "Timestamp": now,
                        "Username": username.strip(),
                        "Filename": uploaded_file.name
                    }])
                    
                    # Tambahkan data baru
                    updated_df = pd.concat([df_logs, new_log], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    st.toast("Log berhasil disimpan ke Google Sheets!", icon="✅")
                else:
                    st.warning("❌ QR Code tidak terdeteksi pada gambar. Pastikan gambar QRIS terlihat jelas.")
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca gambar: {e}")
