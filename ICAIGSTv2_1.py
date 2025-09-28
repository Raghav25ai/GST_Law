import streamlit as st
import requests
from bs4 import BeautifulSoup
import os, re
import pandas as pd
from urllib.parse import urljoin
from io import BytesIO
from datetime import datetime

# ---------------- CONFIG ----------------
CATEGORY_LINKS = {
    "Central GST": "https://idtc.icai.org/gst_new.php?gst_type=CENTRAL+GOODS+AND+SERVICES+TAX",
    "Integrated GST": "https://idtc.icai.org/gst_new.php?gst_type=INTEGRATED+GOODS+AND+SERVICES+TAX",
    "Union Territory GST": "https://idtc.icai.org/gst_new.php?gst_type=UNION+TERRITORY+GOODS+AND+SERVICES+TAX",
    "Compensation to States": "https://idtc.icai.org/gst_new.php?gst_type=GOODS+AND+SERVICES+TAX+%28COMPENSATION+TO+STATES%29",
    "GST Council Minutes": "https://idtc.icai.org/minutes-gst.php?gst_type=MINUTES+OF+GST+COUNCIL+MEETINGS",
    "GST Press Release": "https://idtc.icai.org/press_release.php",
    "GSTN Advisory": "https://idtc.icai.org/gstn-advisory.php",
    "State GST Websites": "https://idtc.icai.org/state-gst.php"
}
HEADERS = {"User-Agent": "Mozilla/5.0"}
DOWNLOAD_DIR = "gst_law_pdfs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------------- HELPERS ----------------
def get_pdfs_from_page(url):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    pdfs = []
    for a in soup.find_all("a", href=True):
        if ".pdf" in a["href"].lower():
            name = a.get_text(strip=True) or a["href"].split("/")[-1]
            pdfs.append((name, urljoin(url, a["href"])))
    return pdfs

def download_pdf(name, url, folder):
    os.makedirs(folder, exist_ok=True)
    safe_name = re.sub(r"[^\w\-\.\(\)]", "_", name)[:150]
    path = os.path.join(folder, safe_name + ".pdf")
    if not os.path.exists(path):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            with open(path, "wb") as f:
                f.write(r.content)
        except:
            return None
    return path

# ---------------- STREAMLIT APP ----------------
st.set_page_config(page_title="ICAI GST Law Downloader", layout="wide")
st.markdown("<h1 style='text-align:center; color:#1E90FF;'>📑 ICAI GST Law Downloader</h1>", unsafe_allow_html=True)

# Show clock
st.markdown(f"<h4 style='text-align:center; color:green;'>🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h4>", unsafe_allow_html=True)

choice = st.selectbox("Select GST Category", list(CATEGORY_LINKS.keys()))

if st.button("Fetch PDFs"):
    with st.spinner("Scraping PDFs..."):
        pdfs = get_pdfs_from_page(CATEGORY_LINKS[choice])
        records = []
        folder = os.path.join(DOWNLOAD_DIR, re.sub(r"[^\w]", "_", choice))
        for name, link in pdfs:
            path = download_pdf(name, link, folder)
            records.append({"Category": choice, "Title": name, "PDF Link": link, "File Path": path if path else "Failed"})
        df = pd.DataFrame(records)
        st.success(f"Fetched {len(df)} PDFs for {choice}")
        st.dataframe(df)

        # Download CSV/Excel
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, f"{choice}.csv", "text/csv")

        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button("⬇️ Download Excel", excel_buffer.getvalue(), f"{choice}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
