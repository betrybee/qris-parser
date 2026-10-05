import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
from PIL import Image
from pyzbar.pyzbar import decode

st.set_page_config(page_title="QRIS Parser", page_icon="🔍", layout="centered")

# --- FUNGSI PARSER EMVCO QRIS ---
def parse_qris_payload(payload):
    parsed = {}
    i = 0
    while i < len(payload):
        tag = payload[i:i+2]
        length = int(payload[i+2:i+4])
        value = payload[i+4:i+4+length]
        parsed[tag] = value
        i += 4 + length

    merchant_name = parsed.get("59", "Tidak Ditemukan")
    merchant_city = parsed.get("60", "Tidak Ditemukan")
    
    # Ekstraksi NMID jika ada di Tag 51 atau 26-45
    nmid = "Tidak Ditemukan"
    for tag in range(26, 46):
        tag_str = f"{tag:02d}"
        if tag_str in parsed:
            sub_payload = parsed[tag_str]
            j = 0
            while j < len(sub_payload):
                sub_tag = sub_payload[j:j+2]
                sub_len = int(sub_payload[j+2:j+4])
                sub_val = sub_payload[j+4:j+4+sub_len]
                if sub_tag == "02":  # Tag 02 biasa berisi NMID
                    nmid = sub_val
                    break
                j += 4 + sub_len

    return {
        "Nama Merchant": merchant_name,
        "Kota": merchant_city,
        "NMID": nmid,
        "Payload Mentah": payload
    }

# --- KONEKSI GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(worksheet="Sheet1", ttl=0)
        return data.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=["Timestamp", "Username", "Filename"])

df_logs = load_data()
total_counter = len(df_logs)

# --- HEADER APP ---
st.title("🔍 QRIS Parser App")
st.write("Aplikasi untuk mengekstrak dan membaca informasi detail dari gambar QRIS.")

st.metric(label="📊 Total QRIS Diproses", value=f"{total_counter} Kali")
st.divider()

# --- INPUT FORM ---
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
                img = Image.open(uploaded_file)
                decoded_objects = decode(img)
                
                if decoded_objects:
                    raw_qr = decoded_objects[0].data.decode('utf-8')
                    result = parse_qris_payload(raw_qr)
                    
                    st.success(f"✅ QRIS Berhasil Diproses untuk **{username}**!")
                    
                    # Tampilkan Hasil Secara Rapi Menggunakan Cards / Columns
                    col1, col2 = st.columns(2)
                    col1.metric("Nama Merchant", result["Nama Merchant"])
                    col2.metric("Kota", result["Kota"])
                    
                    st.write(f"**NMID:** `{result['NMID']}`")
                    
                    with st.expander("Lihat Payload Mentah"):
                        st.code(result["Payload Mentah"], language="text")
                    
                    # Simpan Log ke Google Sheets
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_log = pd.DataFrame([{
                        "Timestamp": now,
                        "Username": username.strip(),
                        "Filename": uploaded_file.name
                    }])
                    
                    updated_df = pd.concat([df_logs, new_log], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    st.toast("Log berhasil dicatat!", icon="✅")
                    
                else:
                    st.warning("❌ QR Code tidak terdeteksi pada gambar.")
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
