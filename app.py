import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
from PIL import Image
from pyzbar.pyzbar import decode

st.set_page_config(page_title="QRIS Parser Pro", page_icon="🔍", layout="centered")

# --- FUNGSI ADVANCED EMVCO QRIS PARSER ---
def parse_qris_detail(payload):
    parsed = {}
    i = 0
    while i < len(payload):
        tag = payload[i:i+2]
        length_str = payload[i+2:i+4]
        if not length_str.isdigit():
            break
        length = int(length_str)
        value = payload[i+4:i+4+length]
        parsed[tag] = value
        i += 4 + length

    # Metrik & Detail Spesifik
    merchant_name = parsed.get("59", "Tidak Ditemukan")
    merchant_city = parsed.get("60", "Tidak Ditemukan")
    postal_code = parsed.get("61", "Tidak Ditemukan")
    country_code = parsed.get("58", "ID")
    currency_code = parsed.get("53", "360") # 360 = IDR
    mcc = parsed.get("52", "Tidak Ditemukan") # Merchant Category Code
    
    # Tipe QR (Static vs Dynamic)
    initiation_point = parsed.get("01", "")
    qr_type = "Dynamic (Sekali Pakai / Nominal Otomatis)" if initiation_point == "12" else "Static (Tetap)"
    
    # Nominal Transaksi (jika QR Dynamic)
    transaction_amount = parsed.get("54", "Sesuai Input Pembayar")

    # Ekstraksi NMID & Acquiring Info dari Sub-tag (Tag 26 - 45)
    nmid = "Tidak Ditemukan"
    acquirer_info = "Tidak Ditemukan"
    
    for tag in range(26, 46):
        tag_str = f"{tag:02d}"
        if tag_str in parsed:
            sub_payload = parsed[tag_str]
            j = 0
            while j < len(sub_payload):
                sub_tag = sub_payload[j:j+2]
                sub_len_str = sub_payload[j+2:j+4]
                if not sub_len_str.isdigit():
                    break
                sub_len = int(sub_len_str)
                sub_val = sub_payload[j+4:j+4+sub_len]
                
                if sub_tag == "00":
                    acquirer_info = sub_val
                elif sub_tag == "02": # Tag 02 umum berisi NMID
                    nmid = sub_val
                j += 4 + sub_len

    return {
        "Nama Merchant": merchant_name,
        "Kota": merchant_city,
        "Kode Pos": postal_code,
        "NMID": nmid,
        "Acquirer / Penyelenggara": acquirer_info,
        "Tipe QRIS": qr_type,
        "Nominal Transaksi": f"Rp {transaction_amount}" if transaction_amount != "Sesuai Input Pembayar" else transaction_amount,
        "Kategori Usaha (MCC)": mcc,
        "Kode Negara": country_code,
        "Kode Mata Uang": "IDR (360)" if currency_code == "360" else currency_code,
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
                    details = parse_qris_detail(raw_qr)
                    
                    st.success(f"✅ QRIS Berhasil Diproses untuk **{username}**!")
                    
                    # 1. Ringkasan Utama (Cards)
                    col1, col2 = st.columns(2)
                    col1.metric("🏪 Nama Merchant", details["Nama Merchant"])
                    col2.metric("📍 Kota", details["Kota"])
                    
                    st.write("---")
                    
                    # 2. Detail Informasi Merchant & Transaksi
                    st.subheader("📋 Detail Informasi QRIS")
                    
                    detail_df = pd.DataFrame([
                        {"Kategori": "NMID (National Merchant ID)", "Detail": details["NMID"]},
                        {"Kategori": "Kode Pos", "Detail": details["Kode Pos"]},
                        {"Kategori": "Penyelenggara / Acquirer", "Detail": details["Acquirer / Penyelenggara"]},
                        {"Kategori": "Tipe QRIS", "Detail": details["Tipe QRIS"]},
                        {"Kategori": "Nominal Transaksi", "Detail": details["Nominal Transaksi"]},
                        {"Kategori": "Merchant Category Code (MCC)", "Detail": details["Kategori Usaha (MCC)"]},
                        {"Kategori": "Negara / Mata Uang", "Detail": f"{details['Kode Negara']} / {details['Kode Mata Uang']}"}
                    ])
                    
                    st.table(detail_df)
                    
                    # 3. Disembunyikan: Raw Payload Mentah
                    with st.expander("📄 Lihat Raw Payload Mentah"):
                        st.code(details["Payload Mentah"], language="text")
                    
                    # 4. Simpan Log ke Google Sheets
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
                    st.warning("❌ QR Code tidak terdeteksi pada gambar. Pastikan gambar QRIS terlihat jelas.")
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses gambar: {e}")
