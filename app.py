import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import json

class QRISParser:
    """Class Parser untuk Payload Data QRIS (EMVCo Standard)"""
    CRITERIA_MAP = {
        "UMI": "Usaha Mikro (Micro)",
        "UKE": "Usaha Kecil (Small)",
        "UME": "Usaha Menengah (Medium)",
        "URE": "Usaha Besar (Large)",
        "PSO": "Public Service Obligation (Government/Public Services)"
    }

    ACQUIRER_MAP = {
        "COM.NOBUBANK.WWW": "Bank Nobu",
        "ID.FINPAY.WWW": "Finpay / Telkom",
        "ID.GPNQR": "GPN / Network Operator",
        "ID.CO.QRIS.WWW": "National QRIS Central",
        "COM.BCA.WWW": "Bank BCA",
        "COM.MANDIRI.WWW": "Bank Mandiri",
        "COM.BRI.WWW": "Bank BRI",
        "COM.BNI.WWW": "Bank BNI",
        "COM.DANA.WWW": "DANA",
        "COM.GOPAY.WWW": "GoPay",
        "COM.SHOPEE.WWW": "ShopeePay"
    }

    def __init__(self, raw_qris: str):
        self.raw_qris = raw_qris.strip()
        self.parsed_data = {}

    def parse(self):
        if not self.raw_qris.startswith("000201"):
            raise ValueError("Data QR Code bukan format QRIS yang valid (harus diawali '000201')")

        index = 0
        qris_len = len(self.raw_qris)

        while index < qris_len:
            tag = self.raw_qris[index:index+2]
            length = int(self.raw_qris[index+2:index+4])
            value = self.raw_qris[index+4:index+4+length]

            if 26 <= int(tag) <= 51 or tag == "62":
                self.parsed_data[tag] = self._parse_sub_tlv(value)
            else:
                self.parsed_data[tag] = value

            index += 4 + length

        return self.format_output()

    def _parse_sub_tlv(self, sub_string: str):
        sub_data = {}
        index = 0
        sub_len = len(sub_string)
        while index < sub_len:
            tag = sub_string[index:index+2]
            length = int(sub_string[index+2:index+4])
            value = sub_string[index+4:index+4+length]
            sub_data[tag] = value
            index += 4 + length
        return sub_data

    def format_output(self):
        data = self.parsed_data

        poi = data.get("01", "")
        poi_type = "Static (Input Nominal Manual)" if poi == "11" else "Dynamic (Nominal Otomatis)" if poi == "12" else "Unknown"

        tag_26 = data.get("26", {})
        acquirer_domain = tag_26.get("00", "N/A")
        acquirer_name = self.ACQUIRER_MAP.get(acquirer_domain, acquirer_domain)

        tag_51 = data.get("51", {})
        nmid = tag_51.get("02", "N/A")
        criteria_code = tag_51.get("03", tag_26.get("03", "N/A"))
        criteria_label = self.CRITERIA_MAP.get(criteria_code, criteria_code)

        amount = data.get("54", None)
        formatted_amount = f"Rp {int(amount):,}".replace(",", ".") if amount else "Tidak ada (Static)"

        tag_62 = data.get("62", {})
        terminal_id = tag_62.get("07", "N/A")

        return {
            "Merchant Name": data.get("59", "N/A"),
            "City": data.get("60", "N/A"),
            "Postal Code": data.get("61", "N/A"),
            "NMID": nmid,
            "QRIS Type": poi_type,
            "Amount": formatted_amount,
            "Merchant Criteria": criteria_label,
            "Acquirer/Bank": acquirer_name,
            "MCC": data.get("52", "N/A"),
            "Terminal ID": terminal_id,
            "CRC Checksum": data.get("63", "N/A"),
            "Raw Payload": self.raw_qris
        }

# Streamlit App
st.set_page_config(page_title="QRIS Parser Indonesia", page_icon="💳", layout="centered")

st.title("QRIS Image Parser")
st.write("Upload QRIS.")

uploaded_file = st.file_uploader("Pilih Gambar QRIS (JPG, PNG, JPEG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded QRIS", use_container_width=True)

    st.info("🔍 Membaca QR Code dari gambar...")
    decoded_objects = decode(image)

    if not decoded_objects:
        st.error("❌ QR Code tidak terdeteksi pada gambar. Pastikan gambarnya jelas!")
    else:
        qr_text = decoded_objects[0].data.decode("utf-8")
        st.success("✅ QR Code berhasil dibaca!")

        try:
            parser = QRISParser(qr_text)
            result = parser.parse()

            st.subheader("📊 Hasil Parsing QRIS")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Nama Merchant", value=result["Merchant Name"])
                st.metric(label="Kota", value=result["City"])
                st.metric(label="Jenis QRIS", value=result["QRIS Type"])
            with col2:
                st.metric(label="Nominal Transaksi", value=result["Amount"])
                st.metric(label="NMID", value=result["NMID"])
                st.metric(label="Acquirer/Bank", value=result["Acquirer/Bank"])

            st.markdown("---")
            st.write("**Detail Lengkap Payload:**")
            st.json(result)

        except Exception as e:
            st.error(f"Gagal mem-parsing data QRIS: {e}")
            st.text_area("Raw Data Terdeteksi:", qr_text)
