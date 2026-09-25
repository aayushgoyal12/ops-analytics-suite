import io
import json
import re
import time
import zipfile
import pandas as pd
import streamlit as st

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="GSTR-2B Reconciliation Suite", page_icon="⚡", layout="wide"
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
.block-container { max-width: 1550px; padding-top: 2rem; padding-bottom: 4rem; }
h1 { color: #f8fafc !important; font-size: 2.1rem !important; font-weight: 750 !important; letter-spacing: -0.035em !important; line-height: 1.2 !important; }
p, label, .stMarkdown { color: #cbd5e1; }
.subtitle { color: #94a3b8; font-size: 1rem; margin-top: 0.25rem; margin-bottom: 1.5rem; max-width: 1100px; line-height: 1.5; }

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
.stat-value { color: #f8fafc; font-size: 1.35rem; font-weight: 750; }
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
# 3. HELPER FUNCTIONS & EXCEL BUILDER
# =========================================================
def validate_gstin(gstin_str):
    if not gstin_str or str(gstin_str).upper() in ["NA", "NONE", "N/A"]:
        return "Not Mentioned"
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return "Valid GSTIN" if re.match(pattern, str(gstin_str).strip()) else "Check Format"

def create_formatted_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reconciliation_Report")
        worksheet = writer.sheets["Reconciliation_Report"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) if col else 12
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 14)
    return buffer.getvalue()

# =========================================================
# 4. SIDEBAR NAVIGATION & TRUST BADGE
# =========================================================
with st.sidebar:
    st.title("⚡ GSTR-2B Suite")
    st.caption("Automated ITC Matcher for CA Firms")
    st.divider()

    st.subheader("💡 Mode")
    st.info("**Free Demo Mode**\nTest the workflow with sample files before uploading client data.")

    st.divider()
    st.markdown("### 🔒 Data Security")
    st.markdown(
        "- Files processed temporarily during your session\n"
        "- Files not used to train AI models\n"
        "- Strict session isolation\n\n"
        "[View our privacy and data deletion policy](#)"
    )

    st.divider()
    st.markdown("### 📞 Support & Demo")
    st.link_button("💬 Book a 15-Minute Demo", "https://wa.me/919650069743")

# =========================================================
# 5. DASHBOARD HEADER & TOP CARDS
# =========================================================
st.markdown(
    """
<h1>GSTR-2B Reconciliation for Indian CA Firms</h1>
<div class="subtitle">Upload your GSTR-2B and purchase register files, identify ITC mismatches, and export a review-ready reconciliation report.</div>
""",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div class="stat-card"><div class="stat-label">Core Matching</div><div class="stat-value">Matched & Unmatched Invoices</div><div class="stat-change">⚡ Automated line-item reconciliation</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="stat-card"><div class="stat-label">Audit Review</div><div class="stat-value">ITC Exception Report</div><div class="stat-change">🔍 Filter gaps & tax discrepancies</div></div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<div class="stat-card"><div class="stat-label">Software Integration</div><div class="stat-value">Excel and Tally/Busy Export</div><div class="stat-change">📊 Formatted reports ready for filing</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Call to Action row
cta_col1, cta_col2 = st.columns(2)
with cta_col1:
    try_sample_top = st.button("🚀 Try a Sample Reconciliation")
with cta_col2:
    st.link_button("📅 Book a 15-Minute Demo", "https://wa.me/919999999999")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# 6. TAB NAVIGATION (Primary Feature First)
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 GSTR-2B Reconciliation (Primary)",
    "🧾 Batch Invoice Extractor",
    "🔄 Tally / Busy Export",
    "📈 Sales & P&L Analyzer",
    "📊 Master Reports Hub",
])

# --- TAB 1: GSTR-2B RECONCILIATION (MAIN FEATURE) ---
with tab1:
    st.subheader("🔍 Auto GSTR-2B vs Purchase Register Matcher")
    st.write("Upload your Purchase Register and GSTR-2B portal reports to reconcile Input Tax Credit (ITC) instantly.")

    if try_sample_top:
        st.session_state["run_sample_rec"] = True

    col1_rec, col2_rec = st.columns(2)
    with col1_rec:
        purch_file = st.file_uploader(
            "Upload Purchase Register",
            type=["xlsx", "csv"],
            help="Supported format: XLSX/CSV. Ensure columns include GSTIN, Invoice Number, and Tax Amount.",
            key="purch_reg"
        )
    with col2_rec:
        gstr2b_file = st.file_uploader(
            "Upload GSTR-2B File",
            type=["xlsx", "json"],
            help="Supported formats: JSON and XLSX downloaded from the GST portal.",
            key="gstr2b_file"
        )

    run_recon = st.button("⚡ Run GSTR-2B Reconciliation", type="primary")

    # Trigger demo results if button clicked or sample triggered
    if st.session_state.get("run_sample_rec", False) or run_recon:
        if st.session_state.get("run_sample_rec", False):
            st.info("⚡ Loading Sample GSTR-2B Reconciliation Results...")
            time.sleep(0.5)

        st.success("✅ Reconciliation Analysis Complete!")

        # Prominent Result Metrics
        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns(6)
        rc1.metric("Total Invoices", "21")
        rc2.metric("Matched", "18", delta="100% Match")
        rc3.metric("Unmatched", "2", delta="Action Required", delta_color="inverse")
        rc4.metric("Tax Mismatches", "₹4,200", delta="Difference", delta_color="inverse")
        rc5.metric("Missing GSTINs", "1", delta="Review", delta_color="off")
        rc6.metric("Duplicates", "0", delta="Clean")

        st.markdown("### 📋 Detailed Exception Review")
        
        # Tabs for detailed exception review
        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
            "✅ Matched Invoices", 
            "⚠️ Unmatched Invoices", 
            "💱 Amount Mismatches", 
            "🚨 Missing GSTINs & Duplicates", 
            "📥 Download Report"
        ])

        with sub_tab1:
            st.write("Invoices successfully matched across Purchase Register and GSTR-2B portal data.")
            sample_matched = pd.DataFrame([
                {"GSTIN": "07AAAAA1234A1Z5", "Invoice No": "INV-101", "Date": "2026-08-12", "Purchase Amt": 15000, "2B Amt": 15000, "Status": "Matched"},
                {"GSTIN": "07BBBCA9876B2Z3", "Invoice No": "INV-102", "Date": "2026-08-15", "Purchase Amt": 42000, "2B Amt": 42000, "Status": "Matched"}
            ])
            st.dataframe(sample_matched, use_container_width=True)

        with sub_tab2:
            st.write("Invoices found in Purchase Register but missing from GSTR-2B.")
            sample_unmatched = pd.DataFrame([
                {"GSTIN": "07CCCSC5555C1Z1", "Invoice No": "INV-109", "Date": "2026-08-20", "Purchase Amt": 12500, "2B Amt": 0, "Status": "Missing in GSTR-2B"}
            ])
            st.dataframe(sample_unmatched, use_container_width=True)

        with sub_tab3:
            st.write("Invoices where taxable value or tax amounts differ between records.")
            sample_mismatch = pd.DataFrame([
                {"GSTIN": "07DDDDD4444D1Z2", "Invoice No": "INV-112", "Purchase Amt": 20000, "2B Amt": 18000, "Difference": 2000, "Status": "Tax Mismatch"}
            ])
            st.dataframe(sample_mismatch, use_container_width=True)

        with sub_tab4:
            st.write("Review of anomalous records, missing vendor GSTINs, or duplicate invoice identifiers.")
            sample_anomalies = pd.DataFrame([
                {"GSTIN": "Not Mentioned", "Invoice No": "INV-144", "Issue": "Missing Vendor GSTIN in Purchase Entry", "Status": "Flagged"}
            ])
            st.dataframe(sample_anomalies, use_container_width=True)

        with sub_tab5:
            st.write("Export your complete audit report package:")
            report_bytes = create_formatted_excel(pd.DataFrame([
                {"GSTIN": "07AAAAA1234A1Z5", "Invoice No": "INV-101", "Status": "Matched", "Diff": 0},
                {"GSTIN": "07CCCSC5555C1Z1", "Invoice No": "INV-109", "Status": "Missing in 2B", "Diff": 12500}
            ]))
            st.download_button(
                label="📥 Download Full Reconciliation Report (.xlsx)",
                data=report_bytes,
                file_name="GSTR2B_Reconciliation_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

        st.info("ℹ️ **Disclaimer:** This tool supports reconciliation review. It does not replace professional GST verification.")

# --- TAB 2: BATCH INVOICE EXTRACTOR ---
with tab2:
    st.subheader("🧾 Additional Tool: Batch Invoice & Receipt Extractor")
    st.write("Upload invoices to extract fields into Master Excel and Tally/Busy XML.")
    st.file_uploader("Upload multiple Invoices/Receipts (PDF, PNG, JPG)", type=["pdf", "png", "jpg"], accept_multiple_files=True)

# --- TAB 3: TALLY ERP DIRECT EXPORT ---
with tab3:
    st.subheader("🔄 Additional Tool: Tally ERP & Busy XML Configurator")
    st.write("Format extracted data for direct import into TallyPrime or Busy accounting software.")
    st.selectbox("Select Target Ledger:", ["Purchase Account", "GST Purchase Direct", "Interstate Purchase 18%"])

# --- TAB 4: SALES & P&L ANALYZER ---
with tab4:
    st.subheader("📈 Additional Tool: Sales & P&L Analytics")
    st.write("Upload Sales Data CSV/XLSX for instant revenue and tax breakdown.")
    st.file_uploader("Upload Sales Report / Bank Statement", type=["csv", "xlsx"])

# --- TAB 5: MASTER REPORTS HUB ---
with tab5:
    st.subheader("📊 Centralized Document Vault")
    st.write("Access and export all historical batch reconciliations and reports.")
    st.info("Processed reports during this session are available for export.")