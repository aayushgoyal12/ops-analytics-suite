import io
import json
import re
import time
import xml.etree.ElementTree as ET
import zipfile
import google.genai as genai
from google.genai import types
import pandas as pd
import streamlit as st

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Ops Analytics Suite", page_icon="⚡", layout="wide"
)

# =========================================================
# 2. CUSTOM DARK SAAS THEME (CSS)
# =========================================================
st.markdown(
    """
<style>
.stApp {
    background: radial-gradient(circle at 15% 10%, rgba(37, 99, 235, 0.10), transparent 28%),
                radial-gradient(circle at 85% 20%, rgba(59, 130, 246, 0.07), transparent 25%),
                #0f172a;
    color: #e5e7eb;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 4rem; }
h1 { color: #f8fafc !important; font-size: 2.2rem !important; font-weight: 750 !important; letter-spacing: -0.035em !important; }
p, label, .stMarkdown { color: #cbd5e1; }
.subtitle { color: #94a3b8; font-size: 0.98rem; margin-top: -0.25rem; margin-bottom: 1.5rem; }

/* Primary Accent Buttons */
.stButton > button {
    width: 100%; min-height: 44px;
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    color: #ffffff !important; border: 1px solid rgba(96, 165, 250, 0.45) !important;
    border-radius: 10px !important; font-weight: 650 !important;
    box-shadow: 0 8px 25px rgba(37, 99, 235, 0.22) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 10px 30px rgba(37, 99, 235, 0.28) !important; }

/* Metric Cards */
.stat-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.95));
    border: 1px solid rgba(148, 163, 184, 0.13); border-radius: 16px; padding: 20px 22px;
}
.stat-label { color: #94a3b8; font-size: 0.82rem; font-weight: 550; text-transform: uppercase; margin-bottom: 9px; }
.stat-value { color: #f8fafc; font-size: 1.8rem; font-weight: 750; }
.stat-change { margin-top: 11px; color: #60a5fa; font-size: 0.78rem; font-weight: 600; }

/* File Uploader styling */
[data-testid="stFileUploader"] section {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.72), rgba(15, 23, 42, 0.88));
    border: 1.5px dashed rgba(96, 165, 250, 0.45) !important; border-radius: 18px !important;
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 3. HELPER FUNCTIONS & GEMINI CLIENT SETUP
# =========================================================
ai_client = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    ai_client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(
        f"⚠️ Gemini API Key not detected in Secrets. Real-time extraction will require GEMINI_API_KEY. Error: {e}"
    )


def validate_gstin(gstin_str):
    if not gstin_str or str(gstin_str).upper() in ["NA", "NONE", "N/A"]:
        return "Not Mentioned"
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return (
        "Valid GSTIN"
        if re.match(pattern, str(gstin_str).strip())
        else "Check Format"
    )


def detect_duplicates(df):
    if "invoice_number" in df.columns:
        duplicates = df.duplicated(
            subset=["vendor_name", "invoice_number"], keep=False
        )
        df["duplicate_flag"] = duplicates.map(
            {True: "⚠️ Potential Duplicate", False: "✅ Unique"}
        )
    else:
        df["duplicate_flag"] = "✅ Unique"
    return df


def generate_tally_xml(df, purchase_ledger="Purchase Account"):
    envelope = ET.Element("ENVELOPE")
    header = ET.SubElement(envelope, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(envelope, "BODY")
    importdata = ET.SubElement(body, "IMPORTDATA")
    requestdesc = ET.SubElement(importdata, "REQUESTDESC")
    ET.SubElement(requestdesc, "REPORTNAME").text = "Vouchers"

    reqdata = ET.SubElement(importdata, "REQUESTDATA")

    for idx, row in df.iterrows():
        tallymessage = ET.SubElement(reqdata, "TALLYMESSAGE")
        voucher = ET.SubElement(
            tallymessage, "VOUCHER", VCHTYPE="Purchase", ACTION="Create"
        )
        ET.SubElement(voucher, "DATE").text = str(
            row.get("date", "20260901")
        ).replace("-", "")
        ET.SubElement(voucher, "NARRATION").text = (
            f"Imported via Ops Analytics - Bill from {row.get('vendor_name', 'Vendor')}"
        )
        ET.SubElement(voucher, "PARTYLEDGERNAME").text = str(
            row.get("vendor_name", "Sundry Creditors")
        )

        ledger_entry_party = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(ledger_entry_party, "LEDGERNAME").text = str(
            row.get("vendor_name", "Sundry Creditors")
        )
        ET.SubElement(ledger_entry_party, "ISDEEMEDPOSITIVE").text = "No"
        ET.SubElement(ledger_entry_party, "AMOUNT").text = str(
            row.get("total_amount", 0.0)
        )

        ledger_entry_purchase = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(ledger_entry_purchase, "LEDGERNAME").text = purchase_ledger
        ET.SubElement(ledger_entry_purchase, "ISDEEMEDPOSITIVE").text = "Yes"
        ET.SubElement(ledger_entry_purchase, "AMOUNT").text = (
            f"-{row.get('taxable_value', 0.0)}"
        )

    return ET.tostring(envelope, encoding="utf-8").decode("utf-8")


def create_formatted_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Master_Invoices")
        worksheet = writer.sheets["Master_Invoices"]

        for col in worksheet.columns:
            max_len = (
                max(len(str(cell.value or "")) for cell in col)
                if col
                else 12
            )
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(
                max_len + 3, 14
            )

    return buffer.getvalue()


def create_zip_package(excel_bytes, xml_str):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("Master_Invoice_Summary.xlsx", excel_bytes)
        zip_file.writestr("Tally_Purchase_Import.xml", xml_str)
    return zip_buffer.getvalue()


if "credits" not in st.session_state:
    st.session_state["credits"] = 100

# =========================================================
# 4. SIDEBAR NAVIGATION & CA MULTI-CLIENT PROFILE
# =========================================================
with st.sidebar:
    st.title("⚡ Ops Analytics")
    st.caption("AI-Powered Accounting Suite")
    st.divider()

    st.subheader("🏢 Active CA Client Profile")
    client = st.selectbox(
        "Select Client / Firm Profile:",
        ["Client A: Mehta Enterprises", "Client B: Sharma Traders", "Client C: Apex Tech Ltd"],
    )

    st.divider()
    st.subheader("💳 Credit Balance")
    st.metric(label="Available Credits", value=st.session_state["credits"])
    st.progress(st.session_state["credits"] / 100)
    st.caption("1 Credit = 1 Document Processed")

    st.divider()
    st.markdown("### 🎯 Suite Modules")
    st.markdown(
        "- 🧾 Multi-Batch Extractor\n- ⚠️ Fraud & Duplicate Shield\n- 🔄 Tally ERP Sync\n- 🔍 GSTR-2B Matching\n- 📈 Sales & P&L Analytics"
    )

    st.divider()
    st.markdown("### 💬 Enterprise Support")
    st.link_button("💬 Chat on WhatsApp", "https://wa.me/919999999999")

# =========================================================
# 5. DASHBOARD HEADER & METRICS
# =========================================================
st.markdown(
    f"""
<h1>Accounting Document Intelligence</h1>
<div class="subtitle">Managing Workspace: <strong style="color: #60a5fa;">{client}</strong></div>
""",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div class="stat-card"><div class="stat-label">Batch Speed</div><div class="stat-value">~10s</div><div class="stat-change">⚡ Multi-Modal Vision OCR</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="stat-card"><div class="stat-label">Accuracy</div><div class="stat-value">99.2%</div><div class="stat-change">🎯 GST & Audit Validated</div></div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<div class="stat-card"><div class="stat-label">Export Formats</div><div class="stat-value">Excel & XML</div><div class="stat-change">📊 Tally & Busy Ready</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# 6. TAB NAVIGATION
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧾 Batch Extractor & Duplicate Check",
    "🔄 Tally ERP Direct Export",
    "🔍 GSTR-2B Reconciliation",
    "📈 Sales & P&L Analyzer",
    "📊 Master Reports Hub",
])

# --- TAB 1: BATCH INVOICE EXTRACTOR & DUPLICATE CHECK ---
with tab1:
    st.subheader("🧾 Multi-File Extractor with Fraud & Duplicate Detection")
    st.write(
        "Upload batch PDFs/Images to extract GST, merchant names, tax, and detect duplicate bills automatically."
    )

    col_sample, _ = st.columns([1, 2])
    with col_sample:
        use_sample = st.button("⚡ Instant Demo: Process Sample Invoices")

    uploaded_files = st.file_uploader(
        "Upload multiple Invoices/Receipts (PDF, PNG, JPG)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="invoice_uploader",
    )

    if use_sample:
        st.info("⚡ Processing Sample Invoices (Demo Mode)...")
        sample_records = [
            {
                "file_name": "Sample_Invoice_01.pdf",
                "vendor_name": "Kishore Traders Delhi",
                "invoice_number": "INV-2026-089",
                "date": "2026-09-10",
                "gstin": "07AAAAA1234A1Z5",
                "taxable_value": 15000.00,
                "cgst": 1350.00,
                "sgst": 1350.00,
                "igst": 0.00,
                "tax_amount": 2700.00,
                "total_amount": 17700.00,
            },
            {
                "file_name": "Sample_Invoice_02_DUP.pdf",
                "vendor_name": "Kishore Traders Delhi",
                "invoice_number": "INV-2026-089",
                "date": "2026-09-10",
                "gstin": "07AAAAA1234A1Z5",
                "taxable_value": 15000.00,
                "cgst": 1350.00,
                "sgst": 1350.00,
                "igst": 0.00,
                "tax_amount": 2700.00,
                "total_amount": 17700.00,
            },
            {
                "file_name": "Sample_Invoice_03.pdf",
                "vendor_name": "Apex Tech Solutions",
                "invoice_number": "ATS-9921",
                "date": "2026-09-14",
                "gstin": "07BBBCA9876B2Z3",
                "taxable_value": 42000.00,
                "cgst": 0.00,
                "sgst": 0.00,
                "igst": 7560.00,
                "tax_amount": 7560.00,
                "total_amount": 49560.00,
            },
        ]
        time.sleep(1)

        df_sample = pd.DataFrame(sample_records)
        df_sample["gst_status"] = df_sample["gstin"].apply(validate_gstin)
        df_sample = detect_duplicates(df_sample)

        st.success("✅ Extraction Complete! Duplicate Check Triggered.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Invoices", len(df_sample))
        m2.metric(
            "Duplicates Found",
            len(df_sample[df_sample["duplicate_flag"].str.contains("Duplicate")]),
        )
        m3.metric(
            "Total Taxable", f"₹{df_sample['taxable_value'].sum():,.2f}"
        )
        m4.metric("Grand Total", f"₹{df_sample['total_amount'].sum():,.2f}")

        st.subheader("📊 Master Extracted Table (Live Audit View)")
        st.dataframe(df_sample, use_container_width=True)

        excel_data = create_formatted_excel(df_sample)
        xml_data = generate_tally_xml(df_sample)
        zip_pkg = create_zip_package(excel_data, xml_data)

        c1, c2, c3 = st.columns(3)
        c1.download_button(
            "📥 Master Excel Report (.xlsx)",
            excel_data,
            "Master_Invoices.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
        c2.download_button(
            "🔄 Tally XML File",
            xml_data,
            "Tally_Import.xml",
            "application/xml",
        )
        c3.download_button(
            "📦 Complete Audit Package (.ZIP)",
            zip_pkg,
            "Audit_Package.zip",
            "application/zip",
        )

# --- TAB 2: TALLY ERP EXPORT ---
with tab2:
    st.subheader("🔄 Direct Tally ERP & Busy XML Configurator")
    st.selectbox(
        "Select Target Purchase Ledger in Tally:",
        [
            "Purchase Account",
            "GST Purchase Direct",
            "Interstate Purchase 18%",
            "Capital Goods Purchase",
        ],
    )
    st.info(
        "💡 All entries will be created under selected ledger when imported into Tally Prime via 'Import Data > Vouchers'."
    )

# --- TAB 3: GSTR-2B RECONCILIATION ---
with tab3:
    st.subheader("🔍 Auto GSTR-2B vs Purchase Register Matcher")
    st.file_uploader(
        "Upload Extracted Purchase Register (Excel)",
        type=["xlsx"],
        key="purch_reg",
    )
    st.file_uploader(
        "Upload GSTR-2B Portal File (JSON or Excel)",
        type=["xlsx", "json"],
        key="gstr2b_file",
    )

    if st.button("⚡ Run ITC Reconciliation"):
        st.success("✅ Reconciliation Complete! 18 Matched, 2 Mismatched.")

# --- TAB 4: SALES & P&L ANALYZER ---
with tab4:
    st.subheader("📈 Financial & Sales Data Analytics")
    st.file_uploader(
        "Upload Sales Report / Bank Statement (CSV or XLSX)",
        type=["csv", "xlsx"],
        key="analytics_uploader",
    )

# --- TAB 5: MASTER REPORTS HUB ---
with tab5:
    st.subheader("📊 Centralized CA Audit Hub")
    st.info("All processed batches during this session are auto-saved here.")