import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# Configuration Page
st.set_page_config(page_title="QRIS Parser", page_icon="🔍", layout="centered")

# 1. Inisialisasi Koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Fungsi untuk membaca data log dari Sheet1
def load_data():
    try:
        data = conn.read(worksheet="Sheet1", ttl=2)
        # Hapus baris yang kosong jika ada
        data = data.dropna(how="all")
        return data
    except Exception:
        return pd.DataFrame(columns=["Timestamp", "Username", "Filename"])

df_logs = load_data()
total_counter = len(df_logs)

# 3. Tampilan Header & Counter
st.title("🔍 QRIS Parser App")
st.write("Aplikasi untuk mengekstrak dan membaca informasi detail dari gambar QRIS.")

# Tampilkan metrik statistik penggunaan
st.metric(label="📊 Total QRIS Diproses", value=f"{total_counter} Kali")

st.divider()

# 4. Input Username & File
username = st.text_input("Username / Nama Pengguna", placeholder="Masukkan nama/username Anda...")
uploaded_file = st.file_uploader("Unggah Gambar QRIS (JPG, PNG, JPEG)", type=["jpg", "jpeg", "png"])

# 5. Eksekusi Parsing & Pencatatan Log
if st.button("Parse QRIS", type="primary"):
    if not username.strip():
        st.error("⚠️ Silakan isi Username Anda terlebih dahulu sebelum memproses.")
    elif uploaded_file is None:
        st.error("⚠️ Silakan unggah gambar QRIS terlebih dahulu.")
    else:
        with st.spinner("Membaca dan memproses QRIS..."):
            # ==========================================
            # LOGIKA PARSING QRIS ANDA (pyzbar/Pillow)
            # ==========================================
            # (Masukkan kode ekstraksi pyzbar yang sudah Anda buat sebelumnya di sini)
            
            # --- CONTOH SIMULASI HASIL ---
            # result = parse_qris_function(uploaded_file)
            st.success(f"QRIS Berhasil Diproses untuk **{username}**!")
            
            # 6. Catat Log Baru ke Google Sheets
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_log = pd.DataFrame([{
                "Timestamp": now,
                "Username": username.strip(),
                "Filename": uploaded_file.name
            }])
            
            updated_df = pd.concat([df_logs, new_log], ignore_index=True)
            
            # Simpan pembaruan ke Google Sheets
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.toast("Aktivitas Anda telah dicatat ke log!", icon="✅")
            st.rerun()  # Refresh halaman agar counter langsung bertambah
