# 🇮🇩 QRIS Image Parser App

A Web Application built with Python and Streamlit to decode and parse Indonesian QRIS (Quick Response Code Indonesian Standard) images.

Developed by [@betrybee](https://github.com/betrybee).

## ✨ Features
- 🖼️ **Image QR Reader**: Extract QR payload directly from uploaded images.
- 🏬 **Merchant Metadata**: Extract Merchant Name, NMID, City, and Postal Code.
- 💳 **Smart Detection**: Detect Static vs Dynamic QRIS.
- 💰 **Amount Parsing**: Formats embedded transaction amounts (IDR).
- 🏦 **Acquirer Recognition**: Detects issuing bank/acquirer and business criteria (UMI, UKE, UME, URE, PSO).

## 🚀 Local Setup

1. Clone this repository:
   ```bash
   git clone [https://github.com/betrybee/qris-parser-app.git](https://github.com/betrybee/qris-parser-app.git)
   cd qris-parser-app