# Pemetaan Kode MCC Umum QRIS di Indonesia
MCC_MAP = {
    "5812": "Eating Places and Restaurants (Restoran / Tempat Makan)",
    "5814": "Fast Food Restaurants (Makanan Cepat Saji)",
    "5411": "Grocery Stores / Supermarkets (Toko Kelontong / Minimarket)",
    "5311": "Department Stores (Toko Serba Ada)",
    "5999": "Miscellaneous and Specialty Retail (Toko Eceran / Retail Umum)",
    "5813": "Drinking Places (Bars, Taverns, Cocktail Lounges, Nightclubs)",
    "7299": "Miscellaneous Personal Services (Layanan Personal)",
}

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

    merchant_name = parsed.get("59", "Tidak Ditemukan")
    merchant_city = parsed.get("60", "Tidak Ditemukan")
    postal_code = parsed.get("61", "Tidak Ditemukan")
    country_code = parsed.get("58", "ID")
    currency_code = parsed.get("53", "360")
    mcc_code = parsed.get("52", "Tidak Ditemukan")
    
    # Keterangan MCC
    mcc_desc = MCC_MAP.get(mcc_code, f"{mcc_code} (Kategori Umum)")

    initiation_point = parsed.get("01", "")
    qr_type = "Dynamic (Sekali Pakai / Nominal Otomatis)" if initiation_point == "12" else "Static (Tetap)"
    transaction_amount = parsed.get("54", "Sesuai Input Pembayar")

    # Ekstraksi NMID & Acquirer yang Presisi
    nmid = "Tidak Ditemukan"
    acquirer_info = "Tidak Ditemukan"
    
    for tag in range(26, 52):
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
                elif sub_tag in ["01", "02", "03"]:
                    # NMID QRIS Indonesia biasa diawali 'ID10...' atau 'ID11...'
                    if sub_val.startswith("ID") or len(sub_val) >= 13:
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
        "Kategori Usaha (MCC)": mcc_desc,
        "Kode Negara": country_code,
        "Kode Mata Uang": "IDR (360)" if currency_code == "360" else currency_code,
        "Payload Mentah": payload
    }
