import streamlit as st
import pandas as pd
import numpy as np


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Sales Dashboard", "Asset Consolidator"])

if page == "Sales Dashboard":
    st.title("Sales Analytics Dashboard")
    # Dashboard code runs here
elif page == "Asset Consolidator":
    st.title("Asset Consolidator")
    # Consolidator code runs here
st.set_page_config(page_title="Operations & Analytics Engine", layout="wide")

st.title("📊 Enterprise Operational & Sales Analytics Engine")
st.write("Upload your raw operational/sales Excel file to extract instant actionable reports.")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.subheader("Raw Data Preview")
    st.dataframe(df.head())

    if st.button("Run Non-Performer Analytics"):
        # Calculate performance
        df["Achievement_%"] = (df["Actual_Units"] / df["Target_Units"]) * 100
        df["Performance_Status"] = np.where(df["Achievement_%"] < 60, "NON-PERFORMER", "ON-TRACK")
        
        st.success("Analysis Complete!")
        
        # Display Non-Performers
        non_performers = df[df["Performance_Status"] == "NON-PERFORMER"]
        st.subheader("🚨 Underperformer Alert List")
        st.dataframe(non_performers)
        
        # Download Option
        output_file = "Processed_Sales_Report.xlsx"
        df.to_excel(output_file, index=False)
        with open(output_file, "rb") as file:
            st.download_button(
                label="📥 Download Full Management Report",
                data=file,
                file_name="Sales_Performance_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )