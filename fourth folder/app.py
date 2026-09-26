import io
import json
import re
import pandas as pd
import streamlit as st


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="GSTR-2B Reconciliation Pro",
    page_icon="⚡",
    layout="wide",
)


# =========================================================
# 2. CUSTOM THEME
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(
                circle at 15% 10%,
                rgba(37, 99, 235, 0.10),
                transparent 28%
            ),
            radial-gradient(
                circle at 85% 20%,
                rgba(59, 130, 246, 0.07),
                transparent 25%
            ),
            #0f172a;
        color: #e5e7eb;
        font-family: Inter, -apple-system, BlinkMacSystemFont,
            "Segoe UI", Roboto, sans-serif;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1 {
        color: #f8fafc !important;
        font-size: 2.2rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.035em !important;
        line-height: 1.2 !important;
    }

    h2, h3 {
        color: #f8fafc !important;
    }

    p, label, .stMarkdown {
        color: #cbd5e1;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.25rem;
        margin-bottom: 1.5rem;
        max-width: 900px;
        line-height: 1.6;
        overflow-wrap: anywhere;
    }

    .stat-card {
        background:
            linear-gradient(
                145deg,
                rgba(30, 41, 59, 0.92),
                rgba(15, 23, 42, 0.95)
            );
        border: 1px solid rgba(148, 163, 184, 0.13);
        border-radius: 16px;
        padding: 20px 22px;
        min-height: 140px;
    }

    .stat-label {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 650;
        text-transform: uppercase;
        margin-bottom: 9px;
        letter-spacing: 0.04em;
    }

    .stat-value {
        color: #f8fafc;
        font-size: 1.3rem;
        font-weight: 750;
        line-height: 1.25;
    }

    .stat-change {
        margin-top: 11px;
        color: #60a5fa;
        font-size: 0.78rem;
        font-weight: 600;
        line-height: 1.4;
    }

    .stButton > button {
        min-height: 44px;
        background:
            linear-gradient(
                135deg,
                #2563eb 0%,
                #3b82f6 100%
            ) !important;
        color: #ffffff !important;
        border: 1px solid rgba(96, 165, 250, 0.45) !important;
        border-radius: 10px !important;
        font-weight: 650 !important;
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.22) !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.28) !important;
    }

    [data-testid="stFileUploader"] section {
        background:
            linear-gradient(
                145deg,
                rgba(30, 41, 59, 0.72),
                rgba(15, 23, 42, 0.88)
            );
        border: 1.5px dashed rgba(96, 165, 250, 0.45) !important;
        border-radius: 18px !important;
    }

    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.60);
        border: 1px solid rgba(148, 163, 184, 0.14);
        padding: 12px;
        border-radius: 12px;
    }

    #MainMenu,
    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. CONFIGURATION
# =========================================================

DEMO_LINK = "https://wa.me/919650069743"


# =========================================================
# 4. HELPER FUNCTIONS
# =========================================================

def clean_column_name(value):
    """Normalize column names for matching."""
    value = str(value).strip().lower()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalize_columns(df):
    """Normalize all dataframe column names."""
    df = df.copy()
    df.columns = [clean_column_name(col) for col in df.columns]
    return df


def find_column(df, aliases):
    """Find the first matching column from a list of aliases."""
    normalized = {
        clean_column_name(col): col
        for col in df.columns
    }

    for alias in aliases:
        alias_clean = clean_column_name(alias)

        if alias_clean in normalized:
            return normalized[alias_clean]

    for column in df.columns:
        for alias in aliases:
            alias_clean = clean_column_name(alias)

            if alias_clean in column or column in alias_clean:
                return column

    return None


def parse_number(value):
    """Convert Indian-style numeric values into floats."""
    if pd.isna(value):
        return 0.0

    text = str(value).strip()
    text = text.replace(",", "")
    text = text.replace("₹", "")
    text = text.replace("Rs.", "")
    text = text.replace("INR", "")

    try:
        return float(text)
    except ValueError:
        return 0.0


def clean_gstin(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().upper()
    value = value.replace(" ", "")

    if value in ["NA", "N/A", "NONE", "NAN", ""]:
        return ""

    return value


def clean_invoice_number(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().upper()
    value = value.replace(" ", "")
    value = value.replace("/", "")
    value = value.replace("-", "")

    return value


def validate_gstin(gstin):
    if not gstin:
        return "Missing"

    pattern = (
        r"^[0-9]{2}[A-Z]{5}[0-9]{4}"
        r"[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    )

    return "Valid" if re.match(pattern, gstin) else "Check"


def read_uploaded_file(uploaded_file):
    """Read CSV, XLSX, or JSON uploaded through Streamlit."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if filename.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)

    if filename.endswith(".json"):
        raw_data = json.load(uploaded_file)

        if isinstance(raw_data, list):
            return pd.json_normalize(raw_data)

        if isinstance(raw_data, dict):
            possible_lists = [
                raw_data.get("data"),
                raw_data.get("items"),
                raw_data.get("records"),
                raw_data.get("b2b"),
            ]

            for value in possible_lists:
                if isinstance(value, list):
                    return pd.json_normalize(value)

            return pd.json_normalize(raw_data)

    raise ValueError("Unsupported file format.")


def prepare_reconciliation_dataframe(df, source_name):
    """
    Convert different input column names into a standard structure.
    Required fields:
    - GSTIN
    - Invoice Number
    - Amount or Tax Amount
    """

    df = normalize_columns(df)

    gstin_col = find_column(
        df,
        [
            "gstin",
            "gstin_of_supplier",
            "supplier_gstin",
            "vendor_gstin",
            "party_gstin",
        ],
    )

    invoice_col = find_column(
        df,
        [
            "invoice_number",
            "invoice_no",
            "invoice_num",
            "inum",
            "document_number",
            "bill_number",
            "bill_no",
        ],
    )

    taxable_col = find_column(
        df,
        [
            "taxable_value",
            "taxable_amount",
            "taxable",
            "txval",
        ],
    )

    tax_col = find_column(
        df,
        [
            "tax_amount",
            "total_tax",
            "tax",
            "iamt",
            "cgst",
            "sgst",
            "igst",
        ],
    )

    total_col = find_column(
        df,
        [
            "total_amount",
            "invoice_value",
            "invoice_amount",
            "total",
            "val",
            "amount",
        ],
    )

    if not gstin_col:
        raise ValueError(
            f"{source_name}: GSTIN column was not found."
        )

    if not invoice_col:
        raise ValueError(
            f"{source_name}: Invoice Number column was not found."
        )

    if not taxable_col and not tax_col and not total_col:
        raise ValueError(
            f"{source_name}: No amount or tax column was found."
        )

    output = pd.DataFrame()

    output["GSTIN"] = df[gstin_col].apply(clean_gstin)
    output["Invoice Number"] = (
        df[invoice_col].apply(clean_invoice_number)
    )

    if taxable_col:
        output["Taxable Value"] = (
            df[taxable_col].apply(parse_number)
        )
    else:
        output["Taxable Value"] = 0.0

    if tax_col:
        output["Tax Amount"] = df[tax_col].apply(parse_number)
    else:
        output["Tax Amount"] = 0.0

    if total_col:
        output["Total Amount"] = (
            df[total_col].apply(parse_number)
        )
    else:
        output["Total Amount"] = (
            output["Taxable Value"] + output["Tax Amount"]
        )

    output["GSTIN Status"] = (
        output["GSTIN"].apply(validate_gstin)
    )
    output["Source"] = source_name

    output = output[
        (output["GSTIN"] != "")
        | (output["Invoice Number"] != "")
    ]

    return output.reset_index(drop=True)


def create_sample_data():
    """Create safe fictional data for demonstration."""
    purchase_register = pd.DataFrame(
        [
            {
                "GSTIN": "07AAAAA1234A1Z5",
                "Invoice Number": "INV-101",
                "Taxable Value": 15000,
                "Tax Amount": 2700,
                "Total Amount": 17700,
            },
            {
                "GSTIN": "07BBBCA9876B2Z3",
                "Invoice Number": "INV-102",
                "Taxable Value": 42000,
                "Tax Amount": 7560,
                "Total Amount": 49560,
            },
            {
                "GSTIN": "07CCCSC5555C1Z1",
                "Invoice Number": "INV-109",
                "Taxable Value": 12500,
                "Tax Amount": 2250,
                "Total Amount": 14750,
            },
            {
                "GSTIN": "07DDDDD4444D1Z2",
                "Invoice Number": "INV-112",
                "Taxable Value": 20000,
                "Tax Amount": 3600,
                "Total Amount": 23600,
            },
        ]
    )

    gstr_2b = pd.DataFrame(
        [
            {
                "GSTIN": "07AAAAA1234A1Z5",
                "Invoice Number": "INV-101",
                "Taxable Value": 15000,
                "Tax Amount": 2700,
                "Total Amount": 17700,
            },
            {
                "GSTIN": "07BBBCA9876B2Z3",
                "Invoice Number": "INV-102",
                "Taxable Value": 42000,
                "Tax Amount": 7560,
                "Total Amount": 49560,
            },
            {
                "GSTIN": "07DDDDD4444D1Z2",
                "Invoice Number": "INV-112",
                "Taxable Value": 18000,
                "Tax Amount": 3240,
                "Total Amount": 21240,
            },
        ]
    )

    return purchase_register, gstr_2b


def reconcile(purchase_df, gstr_df):
    """Match records using GSTIN and Invoice Number."""
    purchase = purchase_df.copy()
    gstr = gstr_df.copy()

    purchase = purchase.rename(
        columns={
            "Taxable Value": "Purchase Taxable Value",
            "Tax Amount": "Purchase Tax Amount",
            "Total Amount": "Purchase Total Amount",
        }
    )

    gstr = gstr.rename(
        columns={
            "Taxable Value": "GSTR Taxable Value",
            "Tax Amount": "GSTR Tax Amount",
            "Total Amount": "GSTR Total Amount",
        }
    )

    match_columns = ["GSTIN", "Invoice Number"]

    result = purchase.merge(
        gstr[
            match_columns
            + [
                "GSTR Taxable Value",
                "GSTR Tax Amount",
                "GSTR Total Amount",
            ]
        ],
        on=match_columns,
        how="outer",
        indicator=True,
    )

    result["Purchase Taxable Value"] = (
        result["Purchase Taxable Value"].fillna(0)
    )

    result["Purchase Tax Amount"] = (
        result["Purchase Tax Amount"].fillna(0)
    )

    result["Purchase Total Amount"] = (
        result["Purchase Total Amount"].fillna(0)
    )

    result["GSTR Taxable Value"] = (
        result["GSTR Taxable Value"].fillna(0)
    )

    result["GSTR Tax Amount"] = (
        result["GSTR Tax Amount"].fillna(0)
    )

    result["GSTR Total Amount"] = (
        result["GSTR Total Amount"].fillna(0)
    )

    taxable_difference = (
        result["Purchase Taxable Value"]
        - result["GSTR Taxable Value"]
    ).abs()

    tax_difference = (
        result["Purchase Tax Amount"]
        - result["GSTR Tax Amount"]
    ).abs()

    if difference := False:
        pass

    statuses = []

    for index, row in result.iterrows():
        merge_status = row["_merge"]

        if merge_status == "left_only":
            statuses.append("Missing in GSTR-2B")

        elif merge_status == "right_only":
            statuses.append("Missing in Purchase Register")

        elif (
            taxable_difference.loc[index] <= 1
            and tax_difference.loc[index] <= 1
        ):
            statuses.append("Matched")

        else:
            statuses.append("Amount Mismatch")

    result["Status"] = statuses

    result["Difference"] = (
        result["Purchase Tax Amount"]
        - result["GSTR Tax Amount"]
    ).abs()

    result = result.drop(columns=["_merge"])

    return result


def create_excel_report(df):
    """Create a downloadable Excel report."""
    buffer = io.BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl",
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Reconciliation Report",
        )

        worksheet = writer.sheets["Reconciliation Report"]

        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                value_length = len(str(cell.value or ""))
                max_length = max(max_length, value_length)

            worksheet.column_dimensions[column_letter].width = (
                max(max_length + 3, 14)
            )

    return buffer.getvalue()


# =========================================================
# 5. SIDEBAR
# =========================================================

with st.sidebar:
    st.title("⚡ GSTR-2B Pro")
    st.caption("ITC Reconciliation for CA Firms")
    st.divider()

    st.subheader("💡 Demo Mode")
    st.info(
        "Use the sample button to see how the reconciliation "
        "workflow works before uploading real files."
    )

    st.divider()

    st.subheader("🔒 Data Security")
    st.markdown(
        """
        - Files are processed during your session
        - Do not upload data you are not authorised to process
        - Use sample or sanitised data during testing
        """
    )

    st.divider()

    st.subheader("📞 Support & Demo")
    st.link_button(
        "Book a 15-Minute Demo",
        DEMO_LINK,
        use_container_width=True,
    )

    st.divider()

    st.caption(
        "This tool supports reconciliation review. "
        "It does not replace professional GST verification."
    )


# =========================================================
# 6. HEADER
# =========================================================

st.markdown(
    """
    <h1>GSTR-2B Reconciliation Pro</h1>
    <div class="subtitle">
        Upload your GSTR-2B and purchase register files, identify ITC
        mismatches, and export a review-ready reconciliation report.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 7. BENEFIT CARDS
# =========================================================

card_1, card_2, card_3 = st.columns(3)

with card_1:
    st.markdown(
        """
        <div class="stat-card">
            <div class="stat-label">CORE MATCHING</div>
            <div class="stat-value">
                Matched & Unmatched
            </div>
            <div class="stat-change">
                Compare invoices across both files
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with card_2:
    st.markdown(
        """
        <div class="stat-card">
            <div class="stat-label">EXCEPTION REVIEW</div>
            <div class="stat-value">
                ITC Mismatch Report
            </div>
            <div class="stat-change">
                Find missing and incorrect records
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with card_3:
    st.markdown(
        """
        <div class="stat-card">
            <div class="stat-label">EXPORT</div>
            <div class="stat-value">
                Excel Report
            </div>
            <div class="stat-change">
                Download results for review
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# 8. CALL TO ACTIONS
# =========================================================

cta_1, cta_2 = st.columns(2)

with cta_1:
    sample_button = st.button(
        "🚀 View Sample Reconciliation",
        use_container_width=True,
    )

with cta_2:
    st.link_button(
        "📅 Book a 15-Minute Demo",
        DEMO_LINK,
        use_container_width=True,
    )


# =========================================================
# 9. FILE UPLOADS
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

st.subheader("🔍 GSTR-2B vs Purchase Register Matcher")

st.write(
    "Upload your Purchase Register and GSTR-2B files to compare "
    "GSTINs, invoice numbers, taxable values, and tax amounts."
)

upload_col_1, upload_col_2 = st.columns(2)

with upload_col_1:
    purchase_file = st.file_uploader(
        "Upload Purchase Register",
        type=["xlsx", "csv"],
        help=(
            "Required fields: GSTIN, Invoice Number, "
            "and at least one amount column."
        ),
    )

with upload_col_2:
    gstr_file = st.file_uploader(
        "Upload GSTR-2B File",
        type=["xlsx", "json"],
        help=(
            "Supported formats: XLSX and JSON. "
            "Required fields: GSTIN, Invoice Number, "
            "and at least one amount column."
        ),
    )


run_button = st.button(
    "⚡ Run GSTR-2B Reconciliation",
    type="primary",
)


# =========================================================
# 10. RECONCILIATION PROCESS
# =========================================================

if sample_button:
    purchase_data, gstr_data = create_sample_data()

    st.info(
        "This is a demonstration using fictional sample data."
    )

    result_df = reconcile(
        purchase_data,
        gstr_data,
    )

    st.session_state["result_df"] = result_df


elif run_button:
    if purchase_file is None or gstr_file is None:
        st.warning(
            "Please upload both the Purchase Register "
            "and GSTR-2B file before running reconciliation."
        )

    else:
        try:
            with st.spinner("Reading and validating your files..."):
                purchase_raw = read_uploaded_file(purchase_file)
                gstr_raw = read_uploaded_file(gstr_file)

                purchase_data = prepare_reconciliation_dataframe(
                    purchase_raw,
                    "Purchase Register",
                )

                gstr_data = prepare_reconciliation_dataframe(
                    gstr_raw,
                    "GSTR-2B",
                )

                result_df = reconcile(
                    purchase_data,
                    gstr_data,
                )

                st.session_state["result_df"] = result_df

            st.success(
                "✅ Reconciliation analysis completed."
            )

        except Exception as error:
            st.error(
                "The files could not be processed. "
                "Please check the required columns and formats."
            )
            st.exception(error)


# =========================================================
# 11. RESULTS
# =========================================================

if "result_df" in st.session_state:
    result_df = st.session_state["result_df"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Reconciliation Summary")

    total_records = len(result_df)
    matched_records = (
        result_df["Status"] == "Matched"
    ).sum()
    unmatched_records = result_df[
        result_df["Status"].isin(
            [
                "Missing in GSTR-2B",
                "Missing in Purchase Register",
            ]
        )
    ].shape[0]
    mismatch_records = (
        result_df["Status"] == "Amount Mismatch"
    ).sum()
    missing_gstin_records = (
        result_df["GSTIN"].astype(str).str.strip() == ""
    ).sum()
    difference_total = result_df["Difference"].sum()

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_4, metric_5, metric_6 = st.columns(3)

    metric_1.metric(
        "Total Records",
        total_records,
    )

    metric_2.metric(
        "Matched",
        matched_records,
    )

    metric_3.metric(
        "Missing Records",
        unmatched_records,
    )

    metric_4.metric(
        "Amount Mismatches",
        mismatch_records,
    )

    metric_5.metric(
        "Missing GSTINs",
        missing_gstin_records,
    )

    metric_6.metric(
        "Total Difference",
        f"₹{difference_total:,.2f}",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("📋 Detailed Exception Review")

    result_filter = st.selectbox(
        "Filter results",
        [
            "All Records",
            "Matched",
            "Missing in GSTR-2B",
            "Missing in Purchase Register",
            "Amount Mismatch",
        ],
    )

    if result_filter == "All Records":
        filtered_result = result_df

    else:
        filtered_result = result_df[
            result_df["Status"] == result_filter
        ]

    st.dataframe(
        filtered_result,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    report_bytes = create_excel_report(result_df)

    st.download_button(
        label="📥 Download Full Reconciliation Report",
        data=report_bytes,
        file_name="GSTR2B_Reconciliation_Report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        type="primary",
        use_container_width=True,
    )

    st.info(
        "Please review all exceptions manually before making "
        "GST or ITC-related decisions."
    )